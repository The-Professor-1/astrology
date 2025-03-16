from django.shortcuts import render, redirect  # type:ignore
from django.http import HttpResponse, HttpResponseForbidden  # type:ignore
from django.contrib import messages  # type:ignore
from django.urls import reverse  # type:ignore
from calculator import library as lb
from .forms import RegisterForm, GeneralForm
from .models import Users, Message_After_Transaction
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
        user = request.user
        try:
            profile = get_object_or_404(UserProfile, user=user)
        except UserProfile.DoesNotExist:
            return HttpResponse("<center><font color='red'><h1>ይህን አገልግሎት ለማግኘት ፈቃድ የሎትም፡፡</h1><br><br></font>"f"<a href='{reverse('nameandnosender')}'><font color='blue'><h2>ፈቃድ ለማግኘት</font></h2></a></center>")
        if profile.status != 'allowed':
            return HttpResponse("<center><font color='red'><h1>ይህን አገልግሎት ለማግኘት ፈቃድ የሎትም፡፡</h1><br><br></font>"f"<a href='{reverse('nameandnosender')}'><font color='blue'><h2>ፈቃድ ለማግኘት</h2></font></a></center>")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def nameandnosender(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect("login")
        action = request.POST.get('action')
        if action == 'send_nameandnumber':
            name = request.POST.get('username')
            if name == 'professor':
                return HttpResponse(f"<center><h1><font color='blue'>እርስዎ የድርጅቱ ባለቤት ስልሆኑ ፈቃድ መጠየቅ አያስፈልግዎትም፡፡</font></h1><br>"f"<font color='blue'><h2><a href='{reverse('calculator_list')}'>ወደ ዋናው ገፅ ለመመለስ</a></h2></font></center>")
            number = request.POST.get('transaction_number')
            status = UserProfile.objects.get(user=request.user).status
            trno = TransactionNumber.objects.filter(transaction_number=number)
            if (len(trno) == 0) and (status == 'denied'):
                try:
                    trno = TransactionNumber(transaction_number=number)
                    trno.save()
                    item = Message_After_Transaction(username=name, transaction_number=number, status=status)
                    item.save()
                    return HttpResponse(f"<center><font color='green'><h1>መልዕክትዎ ተልኳል ውጤቱን ይጠብቁ፡፡</h1><br><br></font>"f"<a href='{reverse('calculator_list')}'><font color='blue'><h2>ወደ ዋናው ገፅ ለመመለስ</font></h2></a></center>")
                except Exception as e:
                    messages.error(request, f"An error occurred: {str(e)}")
                    return HttpResponse(f'<h1>ስህተት አለ፡ {str(e)}</h1>')
            else:
                return HttpResponse(f"<center><font color='red'><h1>የመረጃ ስህተት አለ፡፡ እንደገና ይሞክሩ፡፡</h1><br><br></font>"f"<a href='{reverse('calculator_list')}'><font color='blue'><h2>ወደ ዋናው ገፅ ለመመለስ</font></h2></a></center>")
    return HttpResponse('<h1>Invalid request</h1>')

# Updated calculate_sum with type checking
def calculate_sum(name, modulus, fidel_pairs):
    total_sum = 0
    valid_keys = set().union(*fidel_pairs.keys())  # Flatten all keys into a set
    for char in name:
        if char not in valid_keys:
            return None, char, 'invalid_char'  # Return None for sum, the invalid char, and an error flag
        for key, value in fidel_pairs.items():
            if char in key:
                total_sum = (total_sum + value) % modulus
                break
    return total_sum, None, None  # Sum, no invalid char, no error

# Calculator functions
def kokeb_calculator(name, mother_name, value=KOKEB_MODULUS):
    name_sum, invalid_char_name, error_name = calculate_sum(name, value, lb.fidel_value_pair())
    if error_name:
        return None, invalid_char_name, 'your_name'
    mother_name_sum, invalid_char_mother, error_mother = calculate_sum(mother_name, value, lb.fidel_value_pair())
    if error_mother:
        return None, invalid_char_mother, 'your_mothers_name'
    total_sum = (name_sum + mother_name_sum) % value
    title_list = list(lb.kokeb_disc_pair().keys())
    result = title_list[total_sum - 1]
    return result, "".join(name), "".join(mother_name)

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                else:
                    item = Users.objects.filter(selfname=self_name, mothersname=mother_name).first()
                    if item:
                        user = item
                    else:
                        description = lb.kokeb_disc_pair().get(result, 'Default Description')
                        user = Users(selfname="".join(self_name), mothersname="".join(mother_name), sign=result, description=description)
                        user.save()
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        elif action == 'knowsign':
            title = request.POST.get('sign')
            description = Users.objects.filter(sign=title).values_list('description', flat=True).first()
            context = {'sign': title, 'description': description}
            return render(request, 'calculator/description.html', context)
    return render(request, 'calculator/general.html', {
        'form': form, 'user': user, 'address': address, 'kokeb_calculator_visit': stats.kokeb_calculator_visits,
        'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                else:
                    result = lb.wealth_pair()[no]
            except Exception as e:
                messages.error(request, f"Error calculating wealth: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'result': result, 'address': address, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                else:
                    result = lb.behavior_pair()[no]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'result': result, 'address': address, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                else:
                    result = lb.place_luck_pair()[no]
            except Exception as e:
                messages.error(request, f"Error calculating place luck: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'result': result, 'address': address, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                else:
                    result = lb.marriage_luck_pair()[no]
            except Exception as e:
                messages.error(request, f"Error calculating marriage luck: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'result': result, 'address': address, 'error_message': error_message, 'invalid_field': invalid_field
    })

def calculators_list(request):
    stats, created = SiteStats.objects.get_or_create(id=1)
    stats.calculators_list_visits += 1
    stats.save()
    urls = [
        ('calculate', 'ኮከብዎን ለማዎቅ', 'home-big-image.png'),
        ('wealth_calculator', 'የሃብት እጣ ፈንታን ለማወቅ', 'home-big-image.png'),
        ('behavior_calculator', 'ስለ ጠባይ ለማወቅ', 'home-big-image.png'),
        ('place_calculator', 'ስለ መኖሪያ ቦታ ምቹነት', 'home-big-image.png'),
        ('marriage_luck_calculator', 'ስለ ትዳር በረከት ለማወቅ', 'home-big-image.png'),
        ('birth_prophecy', 'ሰለሚወለድ ልጅ ለማዎቅ', 'home-big-image.png'),
        ('pregnancy_prophecy', 'ለተፀነሰ ትንቢት', 'home-big-image.png'),
        ('love_prophecy', 'ስለ ፍቅር ትንቢት', 'home-big-image.png'),
        ('patient_prophecy', 'ስለ በሽተኛ ሁኔታ ለማወቅ', 'home-big-image.png'),
        ('legal_prophecy', 'ስለ ፍርድ ውሳኔ ለማወቅ', 'home-big-image.png'),
        ('marriage_length_prophecy', 'ስለ ትዳር ቆይታ ለማወቅ', 'home-big-image.png'),
        ('enemy_behavior', 'ስለ ጠላት ፀባይ ለማወቅ', 'home-big-image.png'),
        ('life_luck', 'ስለራስ ኑሮ እድል ለማወቅ', 'home-big-image.png'),
        ('military_prophecy', 'ወደ ጦርነት ለሄደ ወይም ለሚሄድ', 'home-big-image.png'),
        ('servant_behavior', 'ስለ ሰራተኛ ጸባይ ለማወቅለማወቅ', 'home-big-image.png'),
    ]
    admin = request.session.get('admin', 0)
    status = request.session.get('status', '')
    return render(request, 'calculator/calculator_list.html', {
        'urls': urls, 'admin': admin, 'status': status, 'calculators_list_visit': stats.calculators_list_visits
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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char_servant}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                    invalid_field = 'servant_name'
                else:
                    no2, invalid_char_your, error_your = calculate_sum(your_name, SERVANT_MODULUS, lb.fidel_value_pair())
                    if error_your:
                        error_message = f"የተሳሳተ ፊደል '{invalid_char_your}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                        invalid_field = 'your_name'
                    else:
                        result = lb.servant_behavior()[str((no + no2) % SERVANT_MODULUS)]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'address': url, 'result': result, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char_husband}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                    invalid_field = 'husbands_name'
                else:
                    no2, invalid_char_wife, error_wife = calculate_sum(wifes_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                    if error_wife:
                        error_message = f"የተሳሳተ ፊደል '{invalid_char_wife}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                        invalid_field = 'wifes_name'
                    else:
                        no3, invalid_char_month, error_month = calculate_sum(pregnancy_month, MARRIAGE_MODULUS, lb.fidel_value_pair())
                        if error_month:
                            error_message = f"የተሳሳተ ፊደል '{invalid_char_month}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                            invalid_field = 'pregnancy_month'
                        else:
                            result = lb.born_prophecy()[str((((no + no2) % MARRIAGE_MODULUS) + no3) % SERVANT_MODULUS)]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'address': url, 'result': result, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char_husband}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                    invalid_field = 'husbands_name'
                else:
                    no2, invalid_char_wife, error_wife = calculate_sum(wifes_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                    if error_wife:
                        error_message = f"የተሳሳተ ፊደል '{invalid_char_wife}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                        invalid_field = 'wifes_name'
                    else:
                        result = lb.love_prophecy()[str((no + no2) % MARRIAGE_MODULUS)]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'address': url, 'result': result, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char_husband}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                    invalid_field = 'husbands_name'
                else:
                    no2, invalid_char_wife, error_wife = calculate_sum(wifes_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                    if error_wife:
                        error_message = f"የተሳሳተ ፊደል '{invalid_char_wife}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                        invalid_field = 'wifes_name'
                    else:
                        result = lb.pregnancy_prophecy()[str((no + no2) % MARRIAGE_MODULUS)]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'address': url, 'result': result, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char_name}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                    invalid_field = 'your_name'
                else:
                    no2, invalid_char_day, error_day = calculate_sum(war_day, WEALTH_MODULUS, lb.fidel_value_pair())
                    if error_day:
                        error_message = f"የተሳሳተ ፊደል '{invalid_char_day}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                        invalid_field = 'day'
                    else:
                        no3, invalid_char_month, error_month = calculate_sum(war_month, WEALTH_MODULUS, lb.fidel_value_pair())
                        if error_month:
                            error_message = f"የተሳሳተ ፊደል '{invalid_char_month}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                            invalid_field = 'war_month'
                        else:
                            result = lb.military_prophecy()[str((((no + no2) % WEALTH_MODULUS) + no3) % WEALTH_MODULUS)]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'address': url, 'result': result, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char_name}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                    invalid_field = 'your_name'
                else:
                    no2, invalid_char_mother, error_mother = calculate_sum(your_mothers_name, BEHAVIOR_MODULUS, lb.fidel_value_pair())
                    if error_mother:
                        error_message = f"የተሳሳተ ፊደል '{invalid_char_mother}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                        invalid_field = 'your_mothers_name'
                    else:
                        result = lb.life_luck_prophecy()[str((no + no2) % BEHAVIOR_MODULUS)]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'address': url, 'result': result, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char_name}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                    invalid_field = 'patient_name'
                else:
                    no2, invalid_char_mother, error_mother = calculate_sum(patient_mother_name, PLACE_MODULUS, lb.fidel_value_pair())
                    if error_mother:
                        error_message = f"የተሳሳተ ፊደል '{invalid_char_mother}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                        invalid_field = 'patient_mother_name'
                    else:
                        no3, invalid_char_month, error_month = calculate_sum(patient_month, PLACE_MODULUS, lb.fidel_value_pair())
                        if error_month:
                            error_message = f"የተሳሳተ ፊደል '{invalid_char_month}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                            invalid_field = 'month'
                        else:
                            patient_year = patient_year % PLACE_MODULUS
                            result = lb.patient_prophecy()[str((((((no + no2) % PLACE_MODULUS) + no3) % PLACE_MODULUS) + patient_year) % PLACE_MODULUS)]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'address': url, 'result': result, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char_judge}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                    invalid_field = 'judge_name'
                else:
                    no2, invalid_char_your, error_your = calculate_sum(your_name, SERVANT_MODULUS, lb.fidel_value_pair())
                    if error_your:
                        error_message = f"የተሳሳተ ፊደል '{invalid_char_your}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                        invalid_field = 'your_name'
                    else:
                        no3, invalid_char_opponent, error_opponent = calculate_sum(opponent_name, SERVANT_MODULUS, lb.fidel_value_pair())
                        if error_opponent:
                            error_message = f"የተሳሳተ ፊደል '{invalid_char_opponent}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                            invalid_field = 'opponent_name'
                        else:
                            result = lb.legal_case_prophecy()[str((((no + no2) % SERVANT_MODULUS) + no3) % SERVANT_MODULUS)]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'address': url, 'result': result, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char_name}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                    invalid_field = 'enemy_name'
                else:
                    result = lb.enemy_behavior()[str(no % BEHAVIOR_MODULUS)]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'address': url, 'result': result, 'error_message': error_message, 'invalid_field': invalid_field
    })

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
                    error_message = f"የተሳሳተ ፊደል '{invalid_char_husband}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                    invalid_field = 'husbands_name'
                else:
                    no2, invalid_char_wife, error_wife = calculate_sum(wifes_name, MARRIAGE_MODULUS, lb.fidel_value_pair())
                    if error_wife:
                        error_message = f"የተሳሳተ ፊደል '{invalid_char_wife}' ገብቷል፡፡ እባክዎ ትክክለኛ ፊደል ይጠቀሙ፡፡"
                        invalid_field = 'wifes_name'
                    else:
                        result = lb.marriage_time()[str((no + no2) % MARRIAGE_MODULUS)]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {
        'form': form, 'address': url, 'result': result, 'error_message': error_message, 'invalid_field': invalid_field
    })