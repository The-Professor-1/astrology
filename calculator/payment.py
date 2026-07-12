"""Telebirr payment verification for premium calculator access."""
import logging
from decimal import Decimal

from django.conf import settings

from telebirr_verify import (
    amount_from_api_total,
    credited_party_matches,
    parse_telebirr_receipt_text,
    verify_telebirr_receipt,
)

logger = logging.getLogger(__name__)


def verify_and_process_payment(receipt_text: str, used_references: set) -> dict:
    """
    Parse Telebirr SMS, verify via API, validate amount and recipient.
    Returns dict: success (bool), message (str), reference (str|None)
    """
    parsed = parse_telebirr_receipt_text(receipt_text)
    if not parsed:
        return {
            'success': False,
            'message': 'የቴሌብር መልዕክቱ ትክክለኛ አይደለም። ከቴሌብር የተላከውን ሙሉ መልዕክት ይጽፉ።',
            'reference': None,
        }

    reference = parsed['reference']
    if reference in used_references:
        return {
            'success': False,
            'message': 'ይህ የክፍያ ቁጥር ቀድሞውኑ ጥቅም ላይ ውሏል።',
            'reference': reference,
        }

    expected_amount = settings.TELEBIRR_PAYMENT_AMOUNT
    if parsed['amount'] != expected_amount:
        return {
            'success': False,
            'message': f'የክፍያ መጠን {expected_amount} ብር መሆን አለበት። የተላከው መጠን {parsed["amount"]} ብር ነው።',
            'reference': reference,
        }

    api_key = settings.TELEBIRR_API_KEY
    if not api_key:
        logger.error('TELEBIRR_API_KEY is not configured')
        return {
            'success': False,
            'message': 'የክፍያ ማረጋገጫ አገልግሎት ጊዜያዊ ተቋርጧል። እባክዎ ቆይተው ይሞክሩ።',
            'reference': reference,
        }

    api_result = verify_telebirr_receipt(reference, api_key)
    if not api_result['success']:
        err = api_result.get('error') or 'Verification failed'
        return {
            'success': False,
            'message': f'ክፍያው አልተረጋገጠም፡ {err}',
            'reference': reference,
        }

    data = api_result.get('data') or {}
    api_amount = amount_from_api_total(data.get('totalPaidAmount', ''))
    if api_amount is not None and api_amount != expected_amount:
        return {
            'success': False,
            'message': f'API የክፍያ መጠን {api_amount} ብር ነው — {expected_amount} ብር መሆን አለበት።',
            'reference': reference,
        }

    if not credited_party_matches(
        data.get('creditedPartyName', ''),
        data.get('creditedPartyAccountNo', ''),
        settings.TELEBIRR_ACCOUNT_HOLDER,
        settings.TELEBIRR_ACCOUNT_NUMBER,
    ):
        return {
            'success': False,
            'message': 'ክፍያው ወደ ትክክለኛው የቴሌብር አካውንት አልተላከም።',
            'reference': reference,
        }

    status = (data.get('transactionStatus') or '').lower()
    if status and status not in ('completed', 'success', 'successful', 'paid'):
        return {
            'success': False,
            'message': f'የክፍያ ሁኔታ፡ {data.get("transactionStatus", "unknown")}',
            'reference': reference,
        }

    return {
        'success': True,
        'message': 'ክፍያዎ ተረጋግጧል! አሁን ሁሉንም አገልግሎቶች መጠቀም ይችላሉ።',
        'reference': reference,
    }
