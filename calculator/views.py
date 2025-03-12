from django.shortcuts import render,redirect # type:ignore
from django.http import HttpResponse # type:ignore
from django.contrib import messages # type:ignore
from django.urls import reverse # type:ignore
from calculator import library as lb
from .forms import RegisterForm,GeneralForm
from .models import Users,Message_After_Transaction
from home.models import User,UserProfile,TransactionNumber
# Constants for modulus values
KOKEB_MODULUS = 12
PLACE_MODULUS = 7
WEALTH_MODULUS = 4
BEHAVIOR_MODULUS = 9
SERVANT_MODULUS = 5
MARRIAGE_MODULUS = 8

# Helper function to calculate sum
def nameandnosender(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect("login")
        action = request.POST.get('action')
        
        if action == 'send_nameandnumber':
            name = request.POST.get('username')
            if name == 'professor':
                return HttpResponse(f"<center><h1><font color='blue'>እርስዎ የድርጅቱ ባለቤት ስልሆኑ ፈቃድ መጠየቅ አያስፈልግዎትም፡፡</font></h1><br>"
                                    f"<font color='blue'><h2><a href='{reverse('calculator_list')}'>ወደ ዋናው ገፅ ለመመለስ</a></h2></font></center>")
            number = request.POST.get('transaction_number')
            status = UserProfile.objects.get(user=request.user).status
            trno = TransactionNumber.objects.filter(transaction_number=number)
            if (len(trno) == 0) and (status == 'denied'):
                try:
                    # Correct field names based on your model
                    trno = TransactionNumber(transaction_number=number)
                    trno.save()
                    item = Message_After_Transaction(username=name, transaction_number=number,status=status)
                    item.save()
                    return HttpResponse(
    f"<center><font color='green'><h1>መልዕክትዎ ተልኳል ውጤቱን ይጠብቁ፡፡</h1><br><br></font>"
    f"<a href='{reverse('calculator_list')}'><font color='blue'><h2>ወደ ዋናው ገፅ ለመመለስ</font></h2></a></center>"
)
                except Exception as e:
                    messages.error(request, f"An error occurred: {str(e)}")
                    return HttpResponse(f'<h1>ስህተት አለ፡ {str(e)}</h1>')  # Show error in response
                # Alternatively, redirect to a different page where messages are displayed
                # return redirect('your_error_page')
            else:
                return HttpResponse(
            f"<center><font color='red'><h1>የመረጃ ስህተት አለ፡፡ እንደገና ይሞክሩ፡፡</h1><br><br></font>"f"<a href='{reverse('calculator_list')}'><font color='blue'><h2>ወደ ዋናው ገፅ ለመመለስ</font></h2></a></center>"
        )

    return HttpResponse('<h1>Invalid request</h1>')  # Handle non-POST requests
def calculate_sum(name, modulus, fidel_pairs):
    """
    Calculate the sum of character values from a name based on a fidel value pair dictionary.
    
    Args:
        name (str or list): The input name to process.
        modulus (int): The modulus value to apply to the sum.
        fidel_pairs (dict): A dictionary mapping character groups to their values.
    
    Returns:
        int: The calculated sum modulo the given modulus.
    """
    total_sum = 0
    for char in name:
        for key, value in fidel_pairs.items():
            if char in key:
                total_sum = (total_sum + value) % modulus
                break
    return total_sum

# Calculator functions
def kokeb_calculator(name, mother_name, value=KOKEB_MODULUS):
    name_sum = calculate_sum(name, value, lb.fidel_value_pair())
    mother_name_sum = calculate_sum(mother_name, value, lb.fidel_value_pair())
    total_sum = (name_sum + mother_name_sum) % value
    title_list = list(lb.kokeb_disc_pair().keys())
    result = title_list[total_sum - 1]
    return result, "".join(name), "".join(mother_name)

def place_calculator(name, spouse_name, place_name):
    name_sum = calculate_sum(name, PLACE_MODULUS, lb.fidel_value_pair())
    spouse_name_sum = calculate_sum(spouse_name, PLACE_MODULUS, lb.fidel_value_pair())
    place_name_sum = calculate_sum(place_name, PLACE_MODULUS, lb.fidel_value_pair())
    total_sum = (name_sum + spouse_name_sum + place_name_sum) % PLACE_MODULUS
    return str(total_sum)

def wealth_calculator(name, mother_name):
    name_sum = calculate_sum(name, WEALTH_MODULUS, lb.fidel_value_pair())
    mother_name_sum = calculate_sum(mother_name, WEALTH_MODULUS, lb.fidel_value_pair())
    total_sum = (name_sum + mother_name_sum) % WEALTH_MODULUS
    return str(total_sum)

def behavior_calculator(name):
    name_sum = calculate_sum(name, BEHAVIOR_MODULUS, lb.fidel_value_pair())
    return str(name_sum)

# Views
def calculate(request):
    form = GeneralForm
    user = None
    address = 'kokeb_calculator'
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'calculate':
            self_name = request.POST.get('your_name').strip()
            mother_name = request.POST.get('your_mothers_name').strip()
            try:
                item = Users.objects.filter(selfname=self_name, mothersname=mother_name).first()
                if item:
                    user = item
                else:
                    result, finalname, finalmothername = kokeb_calculator(self_name, mother_name)
                    description = lb.kokeb_disc_pair().get(result, 'Default Description')
                    user = Users(selfname=finalname, mothersname=finalmothername, sign=result, description=description)
                    user.save()
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        elif action == 'knowsign':
            title = request.POST.get('sign')
            description = Users.objects.filter(sign=title).values_list('description', flat=True).first()
            context = {'sign': title, 'description': description}
            return render(request, 'calculator/description.html', context)
    return render(request, 'calculator/general.html', {'form': form, 'user': user,'address':address})

def wealth_view(request):
    form = GeneralForm()
    result = None
    address = 'wealth_calculator'
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'wealth_calculate':
            self_name = request.POST.get('your_name')
            mother_name = request.POST.get('your_mothers_name')
            try:
                no = wealth_calculator(self_name, mother_name)
                result = lb.wealth_pair()[no]
            except Exception as e:
                messages.error(request, f"Error calculating wealth: {str(e)}")
    return render(request, 'calculator/general.html', {'form': form, 'result': result,'address':address})

def behavior_view(request):
    form = GeneralForm()
    result = None
    address = 'behavior_calculator'
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'behavior_calculate':
            self_name = request.POST.get('your_name')
            try:
                no = behavior_calculator(self_name)
                result = lb.behavior_pair()[no]
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request, 'calculator/general.html', {'form': form, 'result': result,'address':address})

def place_view(request):
    form = GeneralForm()
    result = None
    address = 'place_calculator'
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'place_luck_calculate':
            self_name = request.POST.get('your_name')
            spouse_name = request.POST.get('your_spouse_name')
            place_name = request.POST.get('place_name')
            try:
                no = place_calculator(self_name, spouse_name, place_name)
                result = lb.place_luck_pair()[no]
            except Exception as e:
                messages.error(request, f"Error calculating place luck: {str(e)}")
    return render(request, 'calculator/general.html', {'form': form, 'result': result,'address':address})

def marriage_luck_view(request):
    form = GeneralForm()
    address = 'marriage_luck'
    result = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'marriage_luck_calculate':
            husbands_name = request.POST.get('husbands_name')
            wifes_name = request.POST.get('wifes_name')
            try:
                no = wealth_calculator(husbands_name, wifes_name)
                result = lb.marriage_luck_pair()[no]
            except Exception as e:
                messages.error(request, f"Error calculating marriage luck: {str(e)}")
    return render(request, 'calculator/general.html', {'form': form, 'result': result,'address':address})

def calculators_list(request):
   urls = [
    ('calculate', 'ኮከብዎን ለማዎቅ','home-big-image.png'),
    ('wealth_calculator', 'የሃብት እጣ ፈንታን ለማወቅ','home-big-image.png'),
    ('behavior_calculator', 'ስለ ጠባይ ለማወቅ','home-big-image.png'),
    ('place_calculator', 'ስለ መኖሪያ ቦታ ምቹነት','home-big-image.png'),
    ('marriage_luck_calculator', 'ስለ ትዳር በረከት ለማወቅ','home-big-image.png'),
    ('birth_prophecy', 'ሰለሚወለድ ልጅ ለማዎቅ','home-big-image.png'),
    ('pregnancy_prophecy', 'ለተፀነሰ ትንቢት','home-big-image.png'),
    ('love_prophecy', 'ስለ ፍቅር ትንቢት','home-big-image.png'),
    ('patient_prophecy', 'ስለ በሽተኛ ሁኔታ ለማወቅ','home-big-image.png'),
    ('legal_prophecy', 'ስለ ፍርድ ውሳኔ ለማወቅ','home-big-image.png'),
    ('marriage_length_prophecy', 'ስለ ትዳር ቆይታ ለማወቅ','home-big-image.png'),
    ('enemy_behavior', 'ስለ ጠላት ፀባይ ለማወቅ','home-big-image.png'),
    ('life_luck', 'ስለራስ ኑሮ እድል ለማወቅ','home-big-image.png'),
    ('military_prophecy', 'ወደ ጦርነት ለሄደ ወይም ለሚሄድ','home-big-image.png'),
    ('servant_behavior','ስለ ሰራተኛ ጸባይ ለማወቅለማወቅ','home-big-image.png'),
        ]
   admin = request.session.get('admin', 0)
   status = request.session.get('status','')
   return render(request, 'calculator/calculator_list.html', {'urls': urls, 'admin': admin,'status':status})
# Placeholder views
def servant_behavior(request):
    form = GeneralForm()
    url = 'servant_behavior'
    result = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'servant_calculate':
            servant_name = request.POST.get('servant_name')
            your_name = request.POST.get('your_name')
            try:
                no = calculate_sum(servant_name,SERVANT_MODULUS,lb.fidel_value_pair())
                no2 = calculate_sum(your_name,SERVANT_MODULUS,lb.fidel_value_pair())
                result = lb.servant_behavior()[str((no+no2)%SERVANT_MODULUS)]
                
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request,'calculator/general.html' ,{'form':form,'address':url,'result':result})

def birth_prophecy(request):
    form = GeneralForm()
    url = 'born_prophecy_calculator'
    result = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'born_prophecy_calculate':
            husbands_name = request.POST.get('husbands_name')
            wifes_name = request.POST.get('wifes_name')
            pregnancy_month = request.POST.get('pregnancy_month')
            try:
                no = calculate_sum(husbands_name,MARRIAGE_MODULUS,lb.fidel_value_pair())
                no2 = calculate_sum(wifes_name,MARRIAGE_MODULUS,lb.fidel_value_pair())
                no3 = calculate_sum(pregnancy_month,MARRIAGE_MODULUS,lb.fidel_value_pair())
                result = lb.born_prophecy()[str((((no+no2)%MARRIAGE_MODULUS)+no3)%SERVANT_MODULUS)]
                
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request,'calculator/general.html' ,{'form':form,'address':url,'result':result})

def love_prophecy(request):
    form = GeneralForm()
    url = 'love_prophecy_calculator'
    result = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'love_prophecy_calculate':
            husbands_name = request.POST.get('husbands_name')
            wifes_name = request.POST.get('wifes_name')
            try:
                no = calculate_sum(husbands_name,MARRIAGE_MODULUS,lb.fidel_value_pair())
                no2 = calculate_sum(wifes_name,MARRIAGE_MODULUS,lb.fidel_value_pair())
                result = lb.love_prophecy()[str((no+no2)%MARRIAGE_MODULUS)]
                
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request,'calculator/general.html' ,{'form':form,'address':url,'result':result})

def pregnancy_prophecy(request):
    form = GeneralForm()
    url = 'pregnancy_prophecy_calculator'
    result = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'pregnancy_prophecy_calculate':
            husbands_name = request.POST.get('husbands_name')
            wifes_name = request.POST.get('wifes_name')
            try:
                no = calculate_sum(husbands_name,MARRIAGE_MODULUS,lb.fidel_value_pair())
                no2 = calculate_sum(wifes_name,MARRIAGE_MODULUS,lb.fidel_value_pair())
                result = lb.pregnancy_prophecy()[str((no+no2)%MARRIAGE_MODULUS)]
                
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request,'calculator/general.html' ,{'form':form,'address':url,'result':result})

def military_prophecy(request):
    form = GeneralForm()
    url = 'military_prophecy_calculator'
    result = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'military_prophecy_calculate':
            your_name = request.POST.get('your_name')
            war_day = request.POST.get('day')
            war_month = request.POST.get('war_month')
            try:
                no = calculate_sum(your_name,WEALTH_MODULUS,lb.fidel_value_pair())
                no2 = calculate_sum(war_day,WEALTH_MODULUS,lb.fidel_value_pair())
                no3 = calculate_sum(war_month,WEALTH_MODULUS,lb.fidel_value_pair())
                result = lb.military_prophecy()[str((((no+no2)%WEALTH_MODULUS)+no3)%WEALTH_MODULUS)]
                
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request,'calculator/general.html' ,{'form':form,'address':url,'result':result})
def life_luck(request):
    form = GeneralForm()
    url = 'life_luck_calculator'
    result = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'life_luck_calculate':
            your_name = request.POST.get('your_name')
            your_mothers_name = request.POST.get('your_mothers_name')
            try:
                no = calculate_sum(your_name,BEHAVIOR_MODULUS,lb.fidel_value_pair())
                no2 = calculate_sum(your_mothers_name,BEHAVIOR_MODULUS,lb.fidel_value_pair())      
             
                result = lb.life_luck_prophecy()[str((no+no2)%BEHAVIOR_MODULUS)]
          
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request,'calculator/general.html' ,{'form':form,'address':url,'result':result})

def patient_prophecy(request):
    form = GeneralForm()
    url = 'patient_prophecy_calculator'
    result = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'patient_prophecy_calculate':
            patient_name = request.POST.get('patient_name')
            patient_mother_name = request.POST.get('patient_mother_name')
            patient_month = request.POST.get('month')
            patient_year = int(request.POST.get('year'))
            try:
                no = calculate_sum(patient_name,PLACE_MODULUS,lb.fidel_value_pair())
                no2 = calculate_sum(patient_mother_name,PLACE_MODULUS,lb.fidel_value_pair())
                no3 = calculate_sum(patient_month,PLACE_MODULUS,lb.fidel_value_pair()) 
                patient_year = patient_year % PLACE_MODULUS
                result = lb.patient_prophecy()[str((((((no+no2)%PLACE_MODULUS)+no3)%PLACE_MODULUS)+patient_year)%PLACE_MODULUS)]
                
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request,'calculator/general.html' ,{'form':form,'address':url,'result':result})

def legal_prophecy(request):
    form = GeneralForm()
    url = 'legal_calculator'
    result = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'legal_case_calculate':
            judge_name = request.POST.get('judge_name')
            your_name = request.POST.get('your_name')
            opponent_name = request.POST.get('opponent_name')
            try:
                no = calculate_sum(judge_name,SERVANT_MODULUS,lb.fidel_value_pair())
                no2 = calculate_sum(your_name,SERVANT_MODULUS,lb.fidel_value_pair())
                no3 = calculate_sum(opponent_name,SERVANT_MODULUS,lb.fidel_value_pair())
                result = lb.legal_case_prophecy()[str((((no+no2)%SERVANT_MODULUS)+no3)%SERVANT_MODULUS)]
                
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request,'calculator/general.html' ,{'form':form,'address':url,'result':result})

def enemy_behavior(request):
    form = GeneralForm()
    url = 'enemy_behavior_calculator'
    result = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'enemy_behavior_calculate':
            enemy_name = request.POST.get('enemy_name')
            try:
                no = calculate_sum(enemy_name,BEHAVIOR_MODULUS,lb.fidel_value_pair())     
                result = lb.enemy_behavior()[str(no%BEHAVIOR_MODULUS)]
          
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request,'calculator/general.html' ,{'form':form,'address':url,'result':result})

def marriage_length_prophecy(request):
    form = GeneralForm()
    url = 'marriage_length'
    result = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'marriage_time_calculate':
            husbands_name = request.POST.get('husbands_name')
            wifes_name = request.POST.get('wifes_name')
            try:
                no = calculate_sum(husbands_name,MARRIAGE_MODULUS,lb.fidel_value_pair())
                no2 = calculate_sum(wifes_name,MARRIAGE_MODULUS,lb.fidel_value_pair())
                result = lb.marriage_time()[str((no+no2)%MARRIAGE_MODULUS)]
                
            except Exception as e:
                messages.error(request, f"Error calculating behavior: {str(e)}")
    return render(request,'calculator/general.html' ,{'form':form,'address':url,'result':result})