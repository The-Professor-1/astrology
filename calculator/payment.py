"""Telebirr payment verification for premium calculator access."""
import logging
from decimal import Decimal

from django.conf import settings

from telebirr_verify import (
    credited_party_matches,
    get_api_field,
    parse_telebirr_receipt_text,
    transfer_amount_matches_expected,
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
    if not transfer_amount_matches_expected(data, expected_amount):
        return {
            'success': False,
            'message': f'የተላከው መጠን {expected_amount} ብር መሆን አለበት።',
            'reference': reference,
        }

    credited_name = get_api_field(
        data,
        'creditedPartyName',
        'credited_party_name',
        'creditedPartyAccountHolderName',
    ) or ''
    credited_account = get_api_field(
        data,
        'creditedPartyAccountNo',
        'creditedPartyAccountNumber',
        'credited_party_account_no',
    ) or ''

    if not credited_party_matches(
        credited_name,
        credited_account,
        settings.TELEBIRR_ACCOUNT_HOLDER,
        settings.TELEBIRR_ACCOUNT_NUMBER,
    ):
        return {
            'success': False,
            'message': 'ክፍያው ወደ ትክክለኛው የቴሌብር አካውንት አልተላከም።',
            'reference': reference,
        }

    status = str(data.get('transactionStatus') or data.get('transaction_status') or '').lower()
    failed_statuses = {'failed', 'cancelled', 'canceled', 'reversed', 'declined', 'rejected'}
    if status in failed_statuses:
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
