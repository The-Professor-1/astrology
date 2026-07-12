"""Telebirr payment verification for premium calculator access."""
import logging
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.utils import timezone

from calculator.models import PaymentVerificationRequest
from telebirr_verify import (
    parse_telebirr_receipt_text,
    validate_telebirr_deposit,
    verify_telebirr_receipt,
)

logger = logging.getLogger(__name__)


def normalize_reference(reference: str) -> str:
    return str(reference or '').strip().upper()


def _legacy_receipt_owner(reference: str) -> Optional[str]:
    """Best-effort username for receipts recorded before used_by existed."""
    from calculator.models import Message_After_Transaction

    ref = normalize_reference(reference)
    msg = (
        Message_After_Transaction.objects
        .filter(transaction_number__iexact=ref, status='allowed')
        .order_by('-id')
        .values_list('username', flat=True)
        .first()
    )
    return msg or None


def check_receipt_already_used(reference: str, current_user=None) -> dict:
    """
    Return whether a receipt reference was already used to unlock access.
    Keys: blocked (bool), message (str), owner (str|None)
    """
    ref = normalize_reference(reference)
    if not ref:
        return {'blocked': False, 'message': '', 'owner': None}

    approved = PaymentVerificationRequest.objects.filter(
        parsed_reference__iexact=ref,
        status__in=(
            PaymentVerificationRequest.STATUS_AUTO_APPROVED,
            PaymentVerificationRequest.STATUS_MANUAL_APPROVED,
        ),
    ).select_related('user').first()

    if approved:
        owner = approved.user.username
        if current_user and approved.user_id == current_user.id:
            return {
                'blocked': True,
                'message': 'አስቀድመው ይህን የክፍያ ቁጥር በመለያዎ ጥቅም ላይ አውልደዋል።',
                'owner': owner,
            }
        return {
            'blocked': True,
            'message': f'ይህ የክፍያ ቁጥር በሌላ ተጠቃሚ ({owner}) ቀድሞውኑ ጥቅም ላይ ውሏል።',
            'owner': owner,
        }

    from home.models import TransactionNumber

    txn = TransactionNumber.objects.filter(transaction_number__iexact=ref).select_related('used_by').first()
    if txn:
        owner = txn.used_by.username if txn.used_by else _legacy_receipt_owner(ref)
        if current_user and txn.used_by_id == current_user.id:
            return {
                'blocked': True,
                'message': 'አስቀድመው ይህን የክፍያ ቁጥር በመለያዎ ጥቅም ላይ አውልደዋል።',
                'owner': owner,
            }
        if owner:
            return {
                'blocked': True,
                'message': f'ይህ የክፍያ ቁጥር በሌላ ተጠቃሚ ({owner}) ቀድሞውኑ ጥቅም ላይ ውሏል።',
                'owner': owner,
            }
        return {
            'blocked': True,
            'message': 'ይህ የክፍያ ቁጥር ቀድሞውኑ ጥቅም ላይ ውሏል።',
            'owner': None,
        }

    legacy_owner = _legacy_receipt_owner(ref)
    if legacy_owner:
        if current_user and current_user.username == legacy_owner:
            return {
                'blocked': True,
                'message': 'አስቀድመው ይህን የክፍያ ቁጥር በመለያዎ ጥቅም ላይ አውልደዋል።',
                'owner': legacy_owner,
            }
        return {
            'blocked': True,
            'message': f'ይህ የክፍያ ቁጥር በሌላ ተጠቃሚ ({legacy_owner}) ቀድሞውኑ ጥቅም ላይ ውሏል።',
            'owner': legacy_owner,
        }

    return {'blocked': False, 'message': '', 'owner': None}


def claim_transaction_reference(reference: str, user) -> bool:
    """Record that this user claimed a receipt. Returns False if already claimed by another user."""
    from django.db import IntegrityError
    from home.models import TransactionNumber

    ref = normalize_reference(reference)
    if not ref or not user:
        return False

    existing = TransactionNumber.objects.filter(transaction_number__iexact=ref).select_related('used_by').first()
    if existing:
        return existing.used_by_id == user.id

    other_approved = PaymentVerificationRequest.objects.filter(
        parsed_reference__iexact=ref,
        status__in=(
            PaymentVerificationRequest.STATUS_AUTO_APPROVED,
            PaymentVerificationRequest.STATUS_MANUAL_APPROVED,
        ),
    ).exclude(user=user).exists()
    if other_approved:
        return False

    try:
        TransactionNumber.objects.create(transaction_number=ref, used_by=user)
        return True
    except IntegrityError:
        existing = TransactionNumber.objects.filter(transaction_number__iexact=ref).first()
        return bool(existing and existing.used_by_id == user.id)


def _save_verification_request(
    user,
    receipt_text: str,
    parsed: Optional[dict],
    api_result: Optional[dict],
    validation: Optional[dict],
    status: str,
    failure_reason: str = '',
) -> Optional[PaymentVerificationRequest]:
    parsed = parsed or {}
    api_result = api_result or {}
    validation = validation or {}
    try:
        return PaymentVerificationRequest.objects.create(
            user=user,
            receipt_text=receipt_text,
            parsed_reference=parsed.get('reference') or validation.get('reference') or '',
            parsed_amount=str(parsed.get('amount', '')),
            parsed_recipient=parsed.get('recipient_name', ''),
            api_response={
                'success': api_result.get('success'),
                'error': api_result.get('error'),
                'data': validation.get('api_data') or api_result.get('data') or {},
                'raw_body': api_result.get('raw_body'),
            },
            verification_checks=validation.get('checks') or {},
            failure_reason=failure_reason or validation.get('failure_reason') or '',
            status=status,
        )
    except Exception as exc:
        logger.exception('Could not save PaymentVerificationRequest: %s', exc)
        return None


def verify_and_process_payment(receipt_text: str, user=None) -> dict:
    """
    Parse Telebirr SMS, verify via API, validate amount and recipient.
    Returns dict: success, message, reference, failure_reason, request_id
    """
    parsed = parse_telebirr_receipt_text(receipt_text)
    if not parsed:
        failure = 'SMS parse failed — incomplete or invalid Telebirr message'
        req = None
        db_save_failed = False
        if user:
            req = _save_verification_request(
                user, receipt_text, None, None, None,
                PaymentVerificationRequest.STATUS_REJECTED,
                failure,
            )
            db_save_failed = req is None
        return {
            'success': False,
            'message': 'የቴሌብር መልዕክቱ ትክክለኛ አይደለም። ከቴሌብር የተላከውን ሙሉ መልዕክት ይጽፉ።',
            'reference': None,
            'failure_reason': failure,
            'request_id': req.id if req else None,
            'db_save_failed': db_save_failed,
        }

    reference = normalize_reference(parsed['reference'])
    parsed['reference'] = reference

    reuse = check_receipt_already_used(reference, user)
    if reuse['blocked']:
        failure = f'reference already used: {reference} by {reuse.get("owner") or "unknown"}'
        req = None
        if user:
            req = _save_verification_request(
                user, receipt_text, parsed, None, None,
                PaymentVerificationRequest.STATUS_REJECTED,
                failure,
            )
        return {
            'success': False,
            'message': reuse['message'],
            'reference': reference,
            'failure_reason': failure,
            'request_id': req.id if req else None,
        }

    expected_amount = settings.TELEBIRR_PAYMENT_AMOUNT
    api_key = settings.TELEBIRR_API_KEY
    if not api_key:
        failure = 'TELEBIRR_API_KEY not configured'
        logger.error(failure)
        req = None
        if user:
            req = _save_verification_request(
                user, receipt_text, parsed, None, None,
                PaymentVerificationRequest.STATUS_PENDING,
                failure,
            )
        return {
            'success': False,
            'message': 'የክፍያ ማረጋገጫ አገልግሎት ጊዜያዊ ተቋርጧል። እባክዎ ቆይተው ይሞክሩ።',
            'reference': reference,
            'failure_reason': failure,
            'request_id': req.id if req else None,
        }

    api_result = verify_telebirr_receipt(reference, api_key)
    validation = validate_telebirr_deposit(
        parsed,
        api_result,
        expected_amount,
        settings.TELEBIRR_ACCOUNT_HOLDER,
        settings.TELEBIRR_ACCOUNT_NUMBER,
    )

    if validation['valid']:
        req = None
        if user:
            req = _save_verification_request(
                user, receipt_text, parsed, api_result, validation,
                PaymentVerificationRequest.STATUS_AUTO_APPROVED,
            )
        return {
            'success': True,
            'message': validation['message'],
            'reference': reference,
            'failure_reason': '',
            'request_id': req.id if req else None,
        }

    failure = validation.get('failure_reason') or validation.get('message') or 'Verification failed'
    logger.warning('Payment verification failed for ref %s: %s', reference, failure)
    req = None
    if user:
        req = _save_verification_request(
            user, receipt_text, parsed, api_result, validation,
            PaymentVerificationRequest.STATUS_PENDING,
            failure,
        )
    return {
        'success': False,
        'message': validation['message'],
        'reference': reference,
        'failure_reason': failure,
        'request_id': req.id if req else None,
    }


def approve_payment_request(request_obj: PaymentVerificationRequest) -> bool:
    """Grant access for a pending verification request (admin manual approve)."""
    from home.models import TransactionNumber, UserProfile

    if request_obj.status in (
        PaymentVerificationRequest.STATUS_AUTO_APPROVED,
        PaymentVerificationRequest.STATUS_MANUAL_APPROVED,
    ):
        return False

    reference = request_obj.parsed_reference
    if reference:
        ref = normalize_reference(reference)
        if check_receipt_already_used(ref, request_obj.user)['blocked']:
            return False
        from home.models import TransactionNumber
        TransactionNumber.objects.get_or_create(
            transaction_number=ref,
            defaults={'used_by': request_obj.user},
        )

    profile, _ = UserProfile.objects.get_or_create(
        user=request_obj.user,
        defaults={'status': 'denied'},
    )
    profile.status = 'allowed'
    profile.save()

    request_obj.status = PaymentVerificationRequest.STATUS_MANUAL_APPROVED
    request_obj.reviewed_at = timezone.now()
    request_obj.save(update_fields=['status', 'reviewed_at'])
    return True
