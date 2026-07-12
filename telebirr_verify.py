"""
Telebirr receipt text parser and verification API client.
Used for automatic deposit verification when user sends full Telebirr SMS text.
"""
import re
import logging
from decimal import Decimal
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Full format example (English):
# "Dear Negus You have transferred ETB 1.00 to Selomon Yimer (2519****1212) on 20/02/2026 05:27:51.
#  Your transaction number is DBK10S886V. The service fee is  ETB 0.87 ... Thank you for using telebirr Ethio telecom"
# Full format example (Amharic):
# "ውድ Mohammed ወደ Selomon Yimer(0988****12) 35.00 ብር በ 01/03/2026 05:30:19 ልከዋል። የሂሳብ እንቅስቃሴ ቁጥርዎ DC15AWEJY1 ነዉ። ... በቴሌብር ስለተገለገሉ"
# Oromiffa example:
# "... Gara NIGUS LIBE (2519****8708)tti  Qarshii 100.00 ... ergitanii jirtu. Lakkoofsi sochii maallaqaa keessan DD68N9FL96' dha. ... link ... receipt/DD68N9FL96 ... teelebirr ... Itiyoo telekoom"

# Amount: ETB X.XX (English), Qarshii X.XX (Oromiffa), or X.XX ብር (Amharic – first match wins transfer amount)
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
    if len(text) < 80:
        return None

    text_lower = text.lower()
    text_for_amharic = text  # keep original for Amharic regexes
    for group in _REQUIRED_MARKER_GROUPS:
        if not any(m in text_lower or m in text_for_amharic for m in group):
            return None

    # Amount: ETB (English), Qarshii (Oromiffa), then X.XX ብር (Amharic)
    amount_str = None
    amount_match = _AMOUNT_ETB_RE.search(text)
    if amount_match:
        amount_str = amount_match.group(1)
    if not amount_str:
        amount_match = _AMOUNT_QARSHII_RE.search(text)
        if amount_match:
            amount_str = amount_match.group(1)
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
            'data': body.get('data'),
            'error': err,
        }

    if not body.get('success'):
        err = body.get('error') or body.get('message') or 'Verification failed'
        logger.warning("Telebirr verify API success=false for ref %s: %s", reference, err)
        return {
            'success': False,
            'data': body.get('data'),
            'error': err,
        }

    return {
        'success': True,
        'data': body.get('data'),
        'error': None,
    }


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
