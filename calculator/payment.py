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


def verify_and_process_payment(receipt_text: str, used_references: set, user=None) -> dict:
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

    reference = parsed['reference']
    if reference in used_references:
        failure = f'reference already used: {reference}'
        req = None
        if user:
            req = _save_verification_request(
                user, receipt_text, parsed, None, None,
                PaymentVerificationRequest.STATUS_REJECTED,
                failure,
            )
        return {
            'success': False,
            'message': 'ይህ የክፍያ ቁጥር ቀድሞውኑ ጥቅም ላይ ውሏል።',
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
        TransactionNumber.objects.get_or_create(transaction_number=reference)

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
