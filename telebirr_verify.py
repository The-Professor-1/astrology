"""
Telebirr receipt text parser and verification API client.
Used for automatic deposit verification when user sends full Telebirr SMS text.
"""
import re
import logging
from decimal import Decimal
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# Full format example (English):
# "Dear Negus You have transferred ETB 1.00 to Selomon Yimer (2519****1212) on 20/02/2026 05:27:51.
#  Your transaction number is DBK10S886V. The service fee is  ETB 0.87 ... Thank you for using telebirr Ethio telecom"
# Full format example (Amharic):
# "ውድ Mohammed ወደ Selomon Yimer(0988****12) 35.00 ብር በ 01/03/2026 05:30:19 ልከዋል። የሂሳብ እንቅስቃሴ ቁጥርዎ DC15AWEJY1 ነዉ። ... በቴሌብር ስለተገለገሉ"
# Oromiffa example:
# "... Gara NIGUS LIBE (2519****8708)tti  Qarshii 100.00 ... ergitanii jirtu. Lakkoofsi sochii maallaqaa keessan DD68N9FL96' dha. ... link ... receipt/DD68N9FL96 ... teelebirr ... Itiyoo telekoom"

# Amount: prefer transfer line, then ETB / Qarshii / ብር (skip service-fee lines)
_AMOUNT_TRANSFER_ETB_RE = re.compile(
    r'transferred\s+ETB\s+([0-9]+(?:\.[0-9]{1,2})?)',
    re.IGNORECASE,
)
_AMOUNT_ETB_RE = re.compile(r'\bETB\s+([0-9]+(?:\.[0-9]{1,2})?)\b', re.IGNORECASE)
_AMOUNT_QARSHII_RE = re.compile(r'Qarshii\s+([0-9]+(?:\.[0-9]{1,2})?)', re.IGNORECASE)
_AMOUNT_BIRR_RE = re.compile(r'([0-9]+(?:\.[0-9]{1,2})?)\s*ብር', re.UNICODE)
# Transaction number: English "transaction number is X" / "receipt no. X" or Amharic "ቁጥርዎ X" / "ቁጥር X" or URL receipt/XXX
_TRANSACTION_NUMBER_RE = re.compile(
    r'(?:transaction\s+number|receipt\s+no\.?)\s+is\s+([A-Z0-9]+)',
    re.IGNORECASE
)
_REF_AMHARIC_RE = re.compile(r'ቁጥር(?:ዎ)?\s+([A-Z0-9]{8,})', re.UNICODE)
_REF_URL_RE = re.compile(r'receipt/([A-Z0-9]{8,})', re.IGNORECASE)
# Oromiffa: "Lakkoofsi sochii maallaqaa keessan REF' dha" or short form
_REF_OROMO_RE = re.compile(
    r"maallaqaa\s+keessan\s+([A-Z0-9]{8,})['′'ʼ]?\s*dha",
    re.IGNORECASE,
)
# Recipient: "to Name (number)" (English), "ወደ Name(number)" (Amharic), "Gara NAME (phone)tti" (Oromiffa)
_TO_RECIPIENT_RE = re.compile(r'\bto\s+([^(]+?)\s*\([0-9*]+\s*\)', re.IGNORECASE)
_TO_RECIPIENT_AMHARIC_RE = re.compile(r'ወደ\s+([^(]+?)\s*\([0-9*]+', re.UNICODE)
_TO_RECIPIENT_OROMO_RE = re.compile(r'Gara\s+([^(]+?)\s*\([0-9*]+', re.IGNORECASE)

# Must contain at least one from each group to consider text "full"
_REQUIRED_MARKER_GROUPS = [
    ['transferred', 'ልከዋል', 'ergitanii'],
    ['etb', 'ብር', 'qarshii'],
    ['transaction number', 'receipt', 'ቁጥር', 'receipt/', 'lakkoofsi', 'maallaqaa'],
    ['telebirr', 'ቴሌብር', 'teelebirr', 'itiyoo'],
]


def parse_telebirr_receipt_text(text: str) -> Optional[dict]:
    """
    Parse full Telebirr receipt SMS text (English, Amharic, or Oromiffa).
    Returns dict with keys: amount (Decimal), reference (transaction number), recipient_name (str),
    or None if format is invalid/incomplete.
    """
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    if len(text) < 40:
        return None

    text_lower = text.lower()
    text_for_amharic = text

    # Soft marker check — reference + telebirr/transfer hint is enough
    has_transfer_hint = any(
        m in text_lower or m in text_for_amharic
        for m in ('transferred', 'ልከዋል', 'ergitanii', 'etb', 'ብር', 'qarshii')
    )
    has_telebirr_hint = any(
        m in text_lower or m in text_for_amharic
        for m in ('telebirr', 'ቴሌብር', 'teelebirr', 'itiyoo', 'ethio telecom')
    )
    if not has_transfer_hint and not has_telebirr_hint:
        return None

    # Amount: transfer-specific ETB first, then Qarshii, generic ETB, Amharic birr
    amount_str = None
    amount_match = _AMOUNT_TRANSFER_ETB_RE.search(text)
    if amount_match:
        amount_str = amount_match.group(1)
    if not amount_str:
        amount_match = _AMOUNT_QARSHII_RE.search(text)
        if amount_match:
            amount_str = amount_match.group(1)
    if not amount_str:
        for amount_match in _AMOUNT_ETB_RE.finditer(text):
            # Skip service-fee lines when possible
            window = text[max(0, amount_match.start() - 40):amount_match.end() + 10].lower()
            if 'service fee' in window or 'service charge' in window:
                continue
            amount_str = amount_match.group(1)
            break
    if not amount_str:
        amount_match = _AMOUNT_BIRR_RE.search(text)
        if amount_match:
            amount_str = amount_match.group(1)

    if not amount_str:
        return None

    # Reference: English, Amharic, Oromiffa maallaqaa keessan, then URL receipt/XXX
    reference = None
    ref_match = _TRANSACTION_NUMBER_RE.search(text)
    if ref_match:
        reference = ref_match.group(1).strip()
    if not reference:
        ref_match = _REF_AMHARIC_RE.search(text)
        if ref_match:
            reference = ref_match.group(1).strip()
    if not reference:
        ref_match = _REF_OROMO_RE.search(text)
        if ref_match:
            reference = ref_match.group(1).strip()
    if not reference:
        ref_match = _REF_URL_RE.search(text)
        if ref_match:
            reference = ref_match.group(1).strip()

    if not reference:
        return None

    # Recipient: English "to", Amharic "ወደ", Oromiffa "Gara"
    recipient_name = ''
    recipient_match = _TO_RECIPIENT_RE.search(text)
    if recipient_match:
        recipient_name = (recipient_match.group(1).strip() or '').strip()
    if not recipient_name:
        recipient_match = _TO_RECIPIENT_AMHARIC_RE.search(text)
        if recipient_match:
            recipient_name = (recipient_match.group(1).strip() or '').strip()
    if not recipient_name:
        recipient_match = _TO_RECIPIENT_OROMO_RE.search(text)
        if recipient_match:
            recipient_name = (recipient_match.group(1).strip() or '').strip()

    try:
        amount = Decimal(amount_str)
    except Exception:
        return None

    return {
        'amount': amount,
        'reference': reference,
        'recipient_name': recipient_name,
    }


def verify_telebirr_receipt(reference: str, api_key: str) -> dict:
    """
    Call verifyapi.leulzenebe.pro to verify a Telebirr receipt by reference (transaction number).
    Returns dict:
      - success: bool
      - data: None or dict with payerName, creditedPartyName, totalPaidAmount, receiptNo, paymentDate, transactionStatus, etc.
      - error: str or None
    """
    if not api_key or not reference:
        return {'success': False, 'data': None, 'error': 'Missing API key or reference'}

    url = 'https://verifyapi.leulzenebe.pro/verify-telebirr'
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
    }
    payload = {'reference': reference}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        body = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {}
    except requests.RequestException as e:
        logger.exception("Telebirr verify API request failed: %s", e)
        return {'success': False, 'data': None, 'error': str(e)}
    except ValueError as e:
        logger.exception("Telebirr verify API invalid JSON: %s", e)
        return {'success': False, 'data': None, 'error': 'Invalid response'}

    if not resp.ok:
        err = body.get('error') or body.get('message') or resp.reason or f'HTTP {resp.status_code}'
        logger.warning("Telebirr verify API HTTP %s for ref %s: %s", resp.status_code, reference, err)
        return {
            'success': False,
            'data': normalize_api_data(body.get('data')),
            'error': err,
            'raw_body': body,
        }

    if not body.get('success'):
        err = body.get('error') or body.get('message') or 'Verification failed'
        logger.warning("Telebirr verify API success=false for ref %s: %s", reference, err)
        return {
            'success': False,
            'data': normalize_api_data(body.get('data')),
            'error': err,
            'raw_body': body,
        }

    return {
        'success': True,
        'data': normalize_api_data(body.get('data')),
        'error': None,
        'raw_body': body,
    }


def normalize_api_data(data) -> dict:
    """Flatten nested API payloads so settledAmount / creditedParty* are at top level."""
    if not data:
        return {}
    if not isinstance(data, dict):
        return {}

    merged = dict(data)
    for key in ('receipt', 'transaction', 'data', 'result', 'payload', 'details'):
        nested = data.get(key)
        if isinstance(nested, dict):
            for k, v in nested.items():
                if k not in merged or merged[k] in (None, ''):
                    merged[k] = v

    return merged


def normalize_credited_party_for_comparison(name: str) -> str:
    """Normalize name for comparison: strip, lower, collapse spaces."""
    if not name:
        return ''
    return ' '.join(str(name).strip().lower().split())


def amount_from_api_total(total_paid_str: str) -> Optional[Decimal]:
    """Parse '101.00 Birr' or '101.00' from API amount strings."""
    if not total_paid_str:
        return None
    s = str(total_paid_str).replace('Birr', '').replace('birr', '').strip()
    try:
        return Decimal(s)
    except Exception:
        return None


def get_api_field(data: dict, *keys: str):
    """Return first non-empty value from API data for any of the given keys."""
    if not data or not isinstance(data, dict):
        return None
    for key in keys:
        val = data.get(key)
        if val is not None and str(val).strip() != '':
            return val
    return None


def amount_from_api_settled(data: dict) -> Optional[Decimal]:
    """
    Extract settledAmount from verify API data — the amount credited to the receiver
    (excludes payer service fee). Example: settledAmount=200 Birr, serviceFee=1.74.
    """
    val = get_api_field(data, 'settledAmount', 'settled_amount')
    if val is None:
        return None
    return amount_from_api_total(str(val))


def amount_from_api_transfer(data: dict) -> Optional[Decimal]:
    """
    Extract the transferred/credited amount from verify API data.
    settledAmount is authoritative; other fields may include service fees.
    """
    settled = amount_from_api_settled(data)
    if settled is not None:
        return settled

    if not data or not isinstance(data, dict):
        return None
    for key in (
        'transferredAmount',
        'transferAmount',
        'creditedAmount',
        'transactionAmount',
        'paidAmount',
    ):
        val = data.get(key)
        if val is not None and val != '':
            amt = amount_from_api_total(str(val))
            if amt is not None:
                return amt
    return None


def transfer_amount_matches_expected(api_data: dict, expected: Decimal) -> bool:
    """
    Return True if API confirms the transfer amount matches expected.
    Prefer settledAmount; totalPaidAmount may include service fee on top of transfer.
    """
    settled = amount_from_api_settled(api_data)
    if settled is not None:
        return settled == expected

    transfer_amt = amount_from_api_transfer(api_data)
    if transfer_amt is not None:
        return transfer_amt == expected

    total_paid = amount_from_api_total(str(get_api_field(api_data, 'totalPaidAmount', 'total_paid_amount') or ''))
    if total_paid is None:
        return True  # no amount field — rely on SMS parse + other checks

    if total_paid == expected:
        return True
    if total_paid > expected:
        fee = total_paid - expected
        return fee <= Decimal('10')

    return False


def _first_name(full_name: str) -> str:
    """Extract first name (first word) for comparison."""
    if not full_name:
        return ''
    return (full_name.strip().split() or [''])[0].lower()


def _last4_digits(value: str) -> str:
    """Extract last 4 digits from phone/account string."""
    digits = re.sub(r'\D', '', str(value or ''))
    return digits[-4:] if len(digits) >= 4 else digits


def _last4_from_account(value: str) -> str:
    """
    Last 4 digits for Telebirr account numbers, including masked values like 2519****1212.
    Uses visible trailing digits after asterisks when present.
    """
    s = str(value or '').strip()
    masked = re.search(r'\*+(\d{4})\s*$', s)
    if masked:
        return masked.group(1)
    return _last4_digits(s)


def credited_party_matches(
    api_credited_name: str,
    api_credited_account_no: str,
    expected_holder_name: str,
    expected_account_number: str,
) -> bool:
    """
    Return True if the API credited party (receiver) matches our Telebirr account in settings.
    Match rules: (1) first name of creditedPartyName (e.g. Selomon) matches our holder,
    (2) last 4 digits of creditedPartyAccountNo (e.g. 2519****1212 -> 1212) match ours.
    Both must match when both are configured in settings.
    """
    credited_name = str(api_credited_name or '').strip()
    credited_account = str(api_credited_account_no or '').strip()
    expected_name = str(expected_holder_name or '').strip()
    expected_number = str(expected_account_number or '').strip()

    if not expected_name and not expected_number:
        return False

    if expected_name:
        if _first_name(credited_name) != _first_name(expected_name):
            return False

    if expected_number:
        if not credited_account:
            return False
        if _last4_from_account(expected_number) != _last4_from_account(credited_account):
            return False

    return True


def sms_amount_matches_expected(parsed_amount: Decimal, expected: Decimal) -> bool:
    """SMS amount may show transfer only; allow small fee delta if total debited is shown."""
    if parsed_amount == expected:
        return True
    if parsed_amount > expected and parsed_amount - expected <= Decimal('10'):
        return True
    return False


def transaction_status_is_failed(api_data: dict) -> bool:
    status = str(get_api_field(api_data, 'transactionStatus', 'transaction_status') or '').lower()
    return status in {'failed', 'cancelled', 'canceled', 'reversed', 'declined', 'rejected'}


def extract_credited_party(api_data: dict) -> Tuple[str, str]:
    name = str(get_api_field(
        api_data,
        'creditedPartyName',
        'credited_party_name',
        'creditedPartyAccountHolderName',
    ) or '')
    account = str(get_api_field(
        api_data,
        'creditedPartyAccountNo',
        'creditedPartyAccountNumber',
        'credited_party_account_no',
    ) or '')
    return name, account


def validate_telebirr_deposit(
    parsed: dict,
    api_result: dict,
    expected_amount: Decimal,
    expected_holder: str,
    expected_account: str,
) -> dict:
    """
    Decide if a deposit is valid for automatic unlock.
    Returns dict with keys: valid (bool), message (str), failure_reason (str), checks (dict).
    Approves when API data has matching settledAmount + credited party, even if success flag is false.
    """
    checks = {}
    reference = parsed.get('reference', '')
    api_data = normalize_api_data(api_result.get('data') or {})
    checks['api_success_flag'] = bool(api_result.get('success'))
    checks['api_error'] = api_result.get('error')
    checks['has_api_data'] = bool(api_data)

    if transaction_status_is_failed(api_data):
        status = get_api_field(api_data, 'transactionStatus', 'transaction_status')
        reason = f'transaction status failed: {status}'
        return {
            'valid': False,
            'message': f'የክፍያ ሁኔታ ተሳክቶ አልተጠናቀቀም ({status})።',
            'failure_reason': reason,
            'checks': checks,
            'reference': reference,
            'api_data': api_data,
        }

    settled = amount_from_api_settled(api_data)
    checks['settled_amount'] = str(settled) if settled is not None else None
    amount_ok = transfer_amount_matches_expected(api_data, expected_amount) if api_data else False
    checks['amount_ok'] = amount_ok

    credited_name, credited_account = extract_credited_party(api_data)
    checks['credited_name'] = credited_name
    checks['credited_account'] = credited_account
    recipient_ok = credited_party_matches(
        credited_name,
        credited_account,
        expected_holder,
        expected_account,
    ) if api_data else False
    checks['recipient_ok'] = recipient_ok

    sms_amount = parsed.get('amount')
    checks['sms_amount'] = str(sms_amount) if sms_amount is not None else None
    checks['sms_amount_ok'] = sms_amount_matches_expected(sms_amount, expected_amount) if sms_amount else False

    if api_data and amount_ok and recipient_ok:
        return {
            'valid': True,
            'message': 'ክፍያዎ ተረጋግጧል! አሁን ሁሉንም አገልግሎቶች መጠቀም ይችላሉ።',
            'failure_reason': '',
            'checks': checks,
            'reference': reference,
            'api_data': api_data,
        }

    if not api_result.get('success') and not api_data:
        err = api_result.get('error') or 'API verification failed'
        return {
            'valid': False,
            'message': f'ክፍያው በ API አልተረጋገጠም፡ {err}',
            'failure_reason': f'api_error: {err}',
            'checks': checks,
            'reference': reference,
            'api_data': api_data,
        }

    if api_data and not amount_ok:
        return {
            'valid': False,
            'message': (
                f'የተላከው መጠን {expected_amount} ብር መሆን አለበት። '
                f'API settledAmount: {settled or "unknown"}።'
            ),
            'failure_reason': f'amount mismatch: settled={settled}, expected={expected_amount}',
            'checks': checks,
            'reference': reference,
            'api_data': api_data,
        }

    if api_data and not recipient_ok:
        return {
            'valid': False,
            'message': (
                'ክፍያው ወደ ትክክለኛው Telebirr አካውንት አልተላከም። '
                f'ተቀባይ: {credited_name or "?"} ({credited_account or "?"})።'
            ),
            'failure_reason': (
                f'recipient mismatch: got {credited_name}/{credited_account}, '
                f'expected {_first_name(expected_holder)}/****{_last4_from_account(expected_account)}'
            ),
            'checks': checks,
            'reference': reference,
            'api_data': api_data,
        }

    if not checks['sms_amount_ok']:
        return {
            'valid': False,
            'message': (
                f'የ SMS መጠን {expected_amount} ብር መሆን አለበት። '
                f'የተገኘው: {sms_amount} ብር።'
            ),
            'failure_reason': f'sms amount mismatch: {sms_amount}',
            'checks': checks,
            'reference': reference,
            'api_data': api_data,
        }

    err = api_result.get('error') or 'Unknown verification failure'
    return {
        'valid': False,
        'message': f'ክፍያው አልተረጋግጠም፡ {err}',
        'failure_reason': err,
        'checks': checks,
        'reference': reference,
        'api_data': api_data,
    }
