from django.shortcuts import render, redirect  # type:ignore
from django.http import HttpResponse, HttpResponseForbidden  # type:ignore
from django.contrib import messages  # type:ignore
from django.urls import reverse  # type:ignore
from django.conf import settings  # type:ignore
from calculator import library as lb
from calculator.payment import verify_and_process_payment
from calculator.records import record_calculation, kokeb_result
from calculator.labels import CALCULATOR_LIST, CALCULATOR_DESCRIPTIONS, general_context
from .forms import RegisterForm, GeneralForm
from .models import Message_After_Transaction
from home.models import User, UserProfile, TransactionNumber, SiteStats
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

# Constants for modulus values
KOKEB_MODULUS = 12
PLACE_MODULUS = 7
WEALTH_MODULUS = 4
BEHAVIOR_MODULUS = 9
SERVANT_MODULUS = 5
MARRIAGE_MODULUS = 8

def profile_permission_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        
        # Use session status, which is kept up-to-date by middleware
        status = request.session.get('status', None)
        if status is None:
            # Fallback to database if session doesn't have it yet
            profile = get_object_or_404(UserProfile, user=request.user)
            status = profile.status
            request.session['status'] = status
        
        if status != 'allowed':
            messages.warning(request, 'ይህን አገልግሎት ለማግኘት ፈቃድ የሎትም።')
            return redirect(reverse('calculator_list') + '#unlock')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def _post_field(request, key, default=''):
    """Read POST field from form body or JSON body (Vercel/serverless friendly)."""
    if key in request.POST:
        return request.POST.get(key, default)
    if not hasattr(request, '_json_body_cache'):
        request._json_body_cache = {}
        if request.content_type and 'application/json' in request.content_type:
            try:
                import json
                raw = request.body.decode('utf-8') if request.body else ''
                if raw.strip():
                    request._json_body_cache = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                request._json_body_cache = {}
    val = request._json_body_cache.get(key, default)
    return val if val is not None else default


def nameandnosender(request):
    if request.method != 'POST':
        return redirect('calculator_list')

    wants_json = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('Accept', '')
        or _post_field(request, 'ajax') == '1'
        or (request.content_type and 'application/json' in request.content_type)
    )

    def ajax_response(success, message, status=200, **extra):
        payload = {'success': success, 'message': message, **extra}
        return JsonResponse(payload, status=status)

    try:
        if not request.user.is_authenticated:
            msg = 'ክፍያ ለማረጋገጥ መጀመሪያ መመዝገብ ወይም መግባት አለብዎት።'
            if wants_json:
                return ajax_response(False, msg, status=401)
            messages.error(request, msg)
            return redirect('login')

        username = request.user.username
        if username == 'professor':
            msg = 'እርስዎ የድርጅቱ ባለቤት ስለሆኑ ፈቃድ መጠየቅ አያስፈልግዎትም።'
            if wants_json:
                return ajax_response(True, msg)
            messages.info(request, msg)
            return redirect('calculator_list')

        receipt_text = (_post_field(request, 'telebirr_receipt_text') or '').strip()
        if not receipt_text:
            msg = 'እባክዎ ከቴሌብር የተላከውን ሙሉ መልዕክት ይጽፉ።'
            if wants_json:
                return ajax_response(False, msg)
            messages.error(request, msg)
            return redirect(reverse('calculator_list') + '#unlock')

        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'status': 'denied'},
        )
        if profile.status == 'allowed':
            msg = 'አስቀድመው ፈቃድ አለዎት — ሁሉንም አገልግሎቶች መጠቀም ይችላሉ።'
            if wants_json:
                return ajax_response(True, msg)
            messages.info(request, msg)
            return redirect('calculator_list')

        used_refs = set(TransactionNumber.objects.values_list('transaction_number', flat=True))
        result = verify_and_process_payment(receipt_text, used_refs, user=request.user)

        if not result['success']:
            extra = {
                'failure_reason': result.get('failure_reason', ''),
                'request_id': result.get('request_id'),
            }
            if result.get('db_save_failed'):
                extra['message'] = (
                    result['message']
                    + '\n\n(DB not updated — run migrations on Neon. See scripts/migrate_neon.ps1)'
                )
            if wants_json:
                return ajax_response(False, extra.get('message', result['message']), **extra)
            messages.error(request, result['message'])
            return redirect(reverse('calculator_list') + '#unlock')

        reference = result['reference']
        TransactionNumber.objects.get_or_create(transaction_number=reference)
        profile.status = 'allowed'
        profile.save()
        request.session['status'] = 'allowed'
        request.session.modified = True

        Message_After_Transaction.objects.create(
            username=username,
            transaction_number=reference,
            status='allowed',
        )

        if wants_json:
            return ajax_response(True, result['message'], request_id=result.get('request_id'))
        messages.success(request, result['message'])
        return redirect('calculator_list')

    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception('Payment verification error: %s', exc)
        msg = f'የማረጋገጫ ስህተት፡ {exc}'
        if wants_json:
            return ajax_response(False, msg, status=500, failure_reason=str(exc))
        messages.error(request, msg)
        return redirect(reverse('calculator_list') + '#unlock')

# Updated calculate_sum with type checking
def calculate_sum(name, modulus, fidel_pairs):
    total_sum = 0
    # Ensure fidel_pairs is a dict and flatten keys if necessary
    if not isinstance(fidel_pairs, dict):
        raise ValueError("fidel_pairs must be a dictionary")
    
    valid_keys = set().union(*[k if isinstance(k, (tuple, list, set)) else [k] for k in fidel_pairs.keys()])
    
    # Debug: Print the valid keys and input for inspection
    for char in name:
        if char not in valid_keys:
            return None, char, 'invalid_char'
        for key, value in fidel_pairs.items():
            # Handle if key is a collection (tuple/list/set)
            if isinstance(key, (tuple, list, set)):
                if char in key:
                    total_sum = (total_sum + value) % modulus
                    break
            elif char == key:
                total_sum = (total_sum + value) % modulus
                break
    return total_sum, None, None

# Calculator functions
def kokeb_calculator(name, mother_name, value=KOKEB_MODULUS):
    # Debugging: Print inputs
    print(f"kokeb_calculator - Name: {name}, Mother Name: {mother_name}")
    
    # Calculate sum for name
    name_sum, invalid_char_name, error_name = calculate_sum(name, value, lb.fidel_value_pair())
    print(f"Name result: sum={name_sum}, invalid_char={invalid_char_name}, error={error_name}")
    
    if error_name:
        return None, invalid_char_name, 'your_name'
    
    # Calculate sum for mother_name
    mother_name_sum, invalid_char_mother, error_mother = calculate_sum(mother_name, value, lb.fidel_value_pair())
    print(f"Mother Name result: sum={mother_name_sum}, invalid_char={invalid_char_mother}, error={error_mother}")
    
    if error_mother:
        return None, invalid_char_mother, 'your_mothers_name'
    
    # Combine sums and get result
    total_sum = (name_sum + mother_name_sum) % value
    title_list = list(lb.kokeb_disc_pair().keys())
    print(f"Total sum: {total_sum}, Title list length: {len(title_list)}")
    
    # Ensure total_sum is within bounds
    if total_sum == 0 or total_sum > len(title_list):
        total_sum = 1  # Default to first item if out of bounds (adjust as needed)
    
    result = title_list[total_sum - 1]  # -1 because list is 0-indexed
    print(f"Result: {result}")
    
    return result, None, None  # No invalid chars, no error

def place_calculator(name, spouse_name, place_name):
    name_sum, invalid_char_name, error_name = calculate_sum(name, PLACE_MODULUS, lb.fidel_value_pair())
    if error_name:
        return None, invalid_char_name, 'your_name'
    spouse_name_sum, invalid_char_spouse, error_spouse = calculate_sum(spouse_name, PLACE_MODULUS, lb.fidel_value_pair())
    if error_spouse:
        return None, invalid_char_spouse, 'your_spouse_name'
    place_name_sum, invalid_char_place, error_place = calculate_sum(place_name, PLACE_MODULUS, lb.fidel_value_pair())
    if error_place:
        return None, invalid_char_place, 'place_name'
    total_sum = (name_sum + spouse_name_sum + place_name_sum) % PLACE_MODULUS
    return str(total_sum), None, None

def wealth_calculator(name, mother_name):
    name_sum, invalid_char_name, error_name = calculate_sum(name, WEALTH_MODULUS, lb.fidel_value_pair())
    if error_name:
        return None, invalid_char_name, 'your_name'
    mother_name_sum, invalid_char_mother, error_mother = calculate_sum(mother_name, WEALTH_MODULUS, lb.fidel_value_pair())
    if error_mother:
        return None, invalid_char_mother, 'your_mothers_name'
    total_sum = (name_sum + mother_name_sum) % WEALTH_MODULUS
    return str(total_sum), None, None

def behavior_calculator(name):
    name_sum, invalid_char_name, error_name = calculate_sum(name, BEHAVIOR_MODULUS, lb.fidel_value_pair())
    if error_name:
        return None, invalid_char_name, 'your_name'
    return str(name_sum), None, None

# Views
def calculate(request):
    stats, created = SiteStats.objects.get_or_create(id=1)
    stats.kokeb_calculator_visits += 1
    stats.save()
    form = GeneralForm()
    user = None
    address = 'kokeb_calculator'
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'calculate':
            self_name = request.POST.get('your_name').strip()
            mother_name = request.POST.get('your_mothers_name').strip()
            try:
                result, invalid_char, invalid_field = kokeb_calculator(self_name, mother_name)
                if invalid_char:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                else:
                    user = kokeb_result(result)
                    record_calculation(request, 'kokeb_calculator', {
                        'your_name': self_name,
                        'your_mothers_name': mother_name,
                    }, result)
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        elif action == 'knowsign':
            title = request.POST.get('sign')
            description = lb.kokeb_disc_pair().get(title, '')
            context = {'sign': title, 'description': description}
            return render(request, 'calculator/description.html', context)
    return render(request, 'calculator/general.html', general_context(
        address, form=form, user=user, kokeb_calculator_visit=stats.kokeb_calculator_visits,
        error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def wealth_view(request):
    form = GeneralForm()
    result = None
    address = 'wealth_calculator'
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'wealth_calculate':
            self_name = request.POST.get('your_name')
            mother_name = request.POST.get('your_mothers_name')
            try:
                no, invalid_char, invalid_field = wealth_calculator(self_name, mother_name)
                if invalid_char:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                else:
                    result = lb.wealth_pair()[no]
                    record_calculation(request, 'wealth_calculator', {
                        'your_name': self_name,
                        'your_mothers_name': mother_name,
                    }, result)
            except Exception as e:
                messages.error(request, f"Error calculating wealth: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        address, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def behavior_view(request):
    form = GeneralForm()
    result = None
    address = 'behavior_calculator'
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'behavior_calculate':
            self_name = request.POST.get('your_name')
            try:
                no, invalid_char, invalid_field = behavior_calculator(self_name)
                if invalid_char:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                else:
                    result = lb.behavior_pair()[no]
                    record_calculation(request, 'behavior_calculator', {
                        'your_name': self_name,
                    }, result)
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        address, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def place_view(request):
    form = GeneralForm()
    result = None
    address = 'place_calculator'
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'place_luck_calculate':
            self_name = request.POST.get('your_name')
            spouse_name = request.POST.get('your_spouse_name')
            place_name = request.POST.get('place_name')
            try:
                no, invalid_char, invalid_field = place_calculator(self_name, spouse_name, place_name)
                if invalid_char:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                else:
                    result = lb.place_luck_pair()[no]
                    record_calculation(request, 'place_calculator', {
                        'your_name': self_name,
                        'your_spouse_name': spouse_name,
                        'place_name': place_name,
                    }, result)
            except Exception as e:
                messages.error(request, f"Error calculating place luck: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        address, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def marriage_luck_view(request):
    form = GeneralForm()
    address = 'marriage_luck'
    result = None
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'marriage_luck_calculate':
            husbands_name = request.POST.get('husbands_name')
            wifes_name = request.POST.get('wifes_name')
            try:
                no, invalid_char, invalid_field = wealth_calculator(husbands_name, wifes_name)
                if invalid_char:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                else:
                    result = lb.marriage_luck_pair()[no]
                    record_calculation(request, 'marriage_luck', {
                        'husbands_name': husbands_name,
                        'wifes_name': wifes_name,
                    }, result)
            except Exception as e:
                messages.error(request, f"Error calculating marriage luck: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        address, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

def calculators_list(request):
    stats, created = SiteStats.objects.get_or_create(id=1)
    stats.calculators_list_visits += 1
    stats.save()
    urls = CALCULATOR_LIST
    admin = request.session.get('admin', 0)
    status = request.session.get('status', '')
    return render(request, 'calculator/calculator_list.html', {
        'urls': urls,
        'admin': admin,
        'status': status,
        'calculators_list_visit': stats.calculators_list_visits,
        'telebirr_holder': settings.TELEBIRR_ACCOUNT_HOLDER,
        'telebirr_number': settings.TELEBIRR_ACCOUNT_NUMBER,
        'telebirr_amount': settings.TELEBIRR_PAYMENT_AMOUNT,
        'calculator_descriptions': CALCULATOR_DESCRIPTIONS,
        'payment_verify_url': reverse('nameandnosender'),
    })

@profile_permission_required
def servant_behavior(request):
    form = GeneralForm()
    url = 'servant_behavior'
    result = None
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'servant_calculate':
            servant_name = request.POST.get('servant_name')
            your_name = request.POST.get('your_name')
            try:
                no, invalid_char_servant, error_servant = calculate_sum(servant_name, SERVANT_MODULUS, lb.fidel_value_pair())
                if error_servant:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                    invalid_field = 'servant_name'
                else:
                    no2, invalid_char_your, error_your = calculate_sum(your_name, SERVANT_MODULUS, lb.fidel_value_pair())
                    if error_your:
                        error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                        invalid_field = 'your_name'
                    else:
                        result = lb.servant_behavior()[str((no + no2) % SERVANT_MODULUS)]
                        record_calculation(request, 'servant_behavior', {
                            'your_name': your_name,
                            'servant_name': servant_name,
                        }, result)
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        url, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def birth_prophecy(request):
    form = GeneralForm()
    url = 'born_prophecy_calculator'
    result = None
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'born_prophecy_calculate':
            husbands_name = request.POST.get('husbands_name')
            wifes_name = request.POST.get('wifes_name')
            pregnancy_month = request.POST.get('pregnancy_month')
            try:
                no, invalid_char_husband, error_husband = calculate_sum(husbands_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                if error_husband:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                    invalid_field = 'husbands_name'
                else:
                    no2, invalid_char_wife, error_wife = calculate_sum(wifes_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                    if error_wife:
                        error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                        invalid_field = 'wifes_name'
                    else:
                        no3, invalid_char_month, error_month = calculate_sum(pregnancy_month, MARRIAGE_MODULUS, lb.fidel_value_pair())
                        if error_month:
                            error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                            invalid_field = 'pregnancy_month'
                        else:
                            result = lb.born_prophecy()[str((((no + no2) % MARRIAGE_MODULUS) + no3) % SERVANT_MODULUS)]
                            record_calculation(request, 'born_prophecy_calculator', {
                                'husbands_name': husbands_name,
                                'wifes_name': wifes_name,
                                'pregnancy_month': pregnancy_month,
                            }, result)
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        url, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def love_prophecy(request):
    form = GeneralForm()
    url = 'love_prophecy_calculator'
    result = None
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'love_prophecy_calculate':
            husbands_name = request.POST.get('husbands_name')
            wifes_name = request.POST.get('wifes_name')
            try:
                no, invalid_char_husband, error_husband = calculate_sum(husbands_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                if error_husband:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                    invalid_field = 'husbands_name'
                else:
                    no2, invalid_char_wife, error_wife = calculate_sum(wifes_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                    if error_wife:
                        error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                        invalid_field = 'wifes_name'
                    else:
                        result = lb.love_prophecy()[str((no + no2) % MARRIAGE_MODULUS)]
                        record_calculation(request, 'love_prophecy_calculator', {
                            'husbands_name': husbands_name,
                            'wifes_name': wifes_name,
                        }, result)
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        url, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def pregnancy_prophecy(request):
    form = GeneralForm()
    url = 'pregnancy_prophecy_calculator'
    result = None
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'pregnancy_prophecy_calculate':
            husbands_name = request.POST.get('husbands_name')
            wifes_name = request.POST.get('wifes_name')
            try:
                no, invalid_char_husband, error_husband = calculate_sum(husbands_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                if error_husband:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                    invalid_field = 'husbands_name'
                else:
                    no2, invalid_char_wife, error_wife = calculate_sum(wifes_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                    if error_wife:
                        error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                        invalid_field = 'wifes_name'
                    else:
                        result = lb.pregnancy_prophecy()[str((no + no2) % MARRIAGE_MODULUS)]
                        record_calculation(request, 'pregnancy_prophecy_calculator', {
                            'husbands_name': husbands_name,
                            'wifes_name': wifes_name,
                        }, result)
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        url, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def military_prophecy(request):
    form = GeneralForm()
    url = 'military_prophecy_calculator'
    result = None
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'military_prophecy_calculate':
            your_name = request.POST.get('your_name')
            war_day = request.POST.get('day')
            war_month = request.POST.get('war_month')
            try:
                no, invalid_char_name, error_name = calculate_sum(your_name, WEALTH_MODULUS, lb.fidel_value_pair())
                if error_name:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                    invalid_field = 'your_name'
                else:
                    no2, invalid_char_day, error_day = calculate_sum(war_day, WEALTH_MODULUS, lb.fidel_value_pair())
                    if error_day:
                        error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                        invalid_field = 'day'
                    else:
                        no3, invalid_char_month, error_month = calculate_sum(war_month, WEALTH_MODULUS, lb.fidel_value_pair())
                        if error_month:
                            error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                            invalid_field = 'war_month'
                        else:
                            result = lb.military_prophecy()[str((((no + no2) % WEALTH_MODULUS) + no3) % WEALTH_MODULUS)]
                            record_calculation(request, 'military_prophecy_calculator', {
                                'your_name': your_name,
                                'day': war_day,
                                'war_month': war_month,
                            }, result)
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        url, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def life_luck(request):
    form = GeneralForm()
    url = 'life_luck_calculator'
    result = None
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'life_luck_calculate':
            your_name = request.POST.get('your_name')
            your_mothers_name = request.POST.get('your_mothers_name')
            try:
                no, invalid_char_name, error_name = calculate_sum(your_name, BEHAVIOR_MODULUS, lb.fidel_value_pair())
                if error_name:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                    invalid_field = 'your_name'
                else:
                    no2, invalid_char_mother, error_mother = calculate_sum(your_mothers_name, BEHAVIOR_MODULUS, lb.fidel_value_pair())
                    if error_mother:
                        error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                        invalid_field = 'your_mothers_name'
                    else:
                        result = lb.life_luck_prophecy()[str((no + no2) % BEHAVIOR_MODULUS)]
                        record_calculation(request, 'life_luck_calculator', {
                            'your_name': your_name,
                            'your_mothers_name': your_mothers_name,
                        }, result)
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        url, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def patient_prophecy(request):
    form = GeneralForm()
    url = 'patient_prophecy_calculator'
    result = None
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'patient_prophecy_calculate':
            patient_name = request.POST.get('patient_name')
            patient_mother_name = request.POST.get('patient_mother_name')
            patient_month = request.POST.get('month')
            patient_year = int(request.POST.get('year'))
            try:
                no, invalid_char_name, error_name = calculate_sum(patient_name, PLACE_MODULUS, lb.fidel_value_pair())
                if error_name:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                    invalid_field = 'patient_name'
                else:
                    no2, invalid_char_mother, error_mother = calculate_sum(patient_mother_name, PLACE_MODULUS, lb.fidel_value_pair())
                    if error_mother:
                        error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                        invalid_field = 'patient_mother_name'
                    else:
                        no3, invalid_char_month, error_month = calculate_sum(patient_month, PLACE_MODULUS, lb.fidel_value_pair())
                        if error_month:
                            error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                            invalid_field = 'month'
                        else:
                            patient_year = patient_year % PLACE_MODULUS
                            result = lb.patient_prophecy()[str((((((no + no2) % PLACE_MODULUS) + no3) % PLACE_MODULUS) + patient_year) % PLACE_MODULUS)]
                            record_calculation(request, 'patient_prophecy_calculator', {
                                'patient_name': patient_name,
                                'patient_mother_name': patient_mother_name,
                                'month': patient_month,
                                'year': request.POST.get('year'),
                            }, result)
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        url, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def legal_prophecy(request):
    form = GeneralForm()
    url = 'legal_calculator'
    result = None
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'legal_case_calculate':
            judge_name = request.POST.get('judge_name')
            your_name = request.POST.get('your_name')
            opponent_name = request.POST.get('opponent_name')
            try:
                no, invalid_char_judge, error_judge = calculate_sum(judge_name, SERVANT_MODULUS, lb.fidel_value_pair())
                if error_judge:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                    invalid_field = 'judge_name'
                else:
                    no2, invalid_char_your, error_your = calculate_sum(your_name, SERVANT_MODULUS, lb.fidel_value_pair())
                    if error_your:
                        error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                        invalid_field = 'your_name'
                    else:
                        no3, invalid_char_opponent, error_opponent = calculate_sum(opponent_name, SERVANT_MODULUS, lb.fidel_value_pair())
                        if error_opponent:
                            error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                            invalid_field = 'opponent_name'
                        else:
                            result = lb.legal_case_prophecy()[str((((no + no2) % SERVANT_MODULUS) + no3) % SERVANT_MODULUS)]
                            record_calculation(request, 'legal_calculator', {
                                'judge_name': judge_name,
                                'your_name': your_name,
                                'opponent_name': opponent_name,
                            }, result)
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        url, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def enemy_behavior(request):
    form = GeneralForm()
    url = 'enemy_behavior_calculator'
    result = None
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'enemy_behavior_calculate':
            enemy_name = request.POST.get('enemy_name')
            try:
                no, invalid_char_name, error_name = calculate_sum(enemy_name, BEHAVIOR_MODULUS, lb.fidel_value_pair())
                if error_name:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                    invalid_field = 'enemy_name'
                else:
                    result = lb.enemy_behavior()[str(no % BEHAVIOR_MODULUS)]
                    record_calculation(request, 'enemy_behavior_calculator', {
                        'enemy_name': enemy_name,
                    }, result)
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        url, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))

@profile_permission_required
def marriage_length_prophecy(request):
    form = GeneralForm()
    url = 'marriage_length'
    result = None
    error_message = None
    invalid_field = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'marriage_time_calculate':
            husbands_name = request.POST.get('husbands_name')
            wifes_name = request.POST.get('wifes_name')
            try:
                no, invalid_char_husband, error_husband = calculate_sum(husbands_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                if error_husband:
                    error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                    invalid_field = 'husbands_name'
                else:
                    no2, invalid_char_wife, error_wife = calculate_sum(wifes_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                    if error_wife:
                        error_message = f"የተሳሳተ ፊደል አስገብተዋል፡፡ እባክዎ በአማርኛ ብቻ ያስገቡ፡፡"
                        invalid_field = 'wifes_name'
                    else:
                        result = lb.marriage_time()[str((no + no2) % MARRIAGE_MODULUS)]
                        record_calculation(request, 'marriage_length', {
                            'husbands_name': husbands_name,
                            'wifes_name': wifes_name,
                        }, result)
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', general_context(
        url, form=form, result=result, error_message=error_message, invalid_field=invalid_field,
    ))