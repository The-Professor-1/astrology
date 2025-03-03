from django import forms # type: ignore
from django.contrib.auth.models import User # type:ignore

class GeneralForm(forms.Form):
    OPTIONS = [
        ('መስከረም', 'መስከረም'),
        ('ጥቅምት', 'ጥቅምት'),
        ('ህዳር', 'ህዳር'),
        ('ታህሳስ', 'ታህሳስ'),
        ('ጥር', 'ጥር'),
        ('የካቲት', 'የካቲት'),
        ('መጋቢት', 'መጋቢት'),
        ('ሚያዚያ', 'ሚያዚያ'),
        ('ግንቦት', 'ግንቦት'),
        ('ሰኔ', 'ሰኔ'),
        ('ሃምሌ', 'ሃምሌ'),
        ('ነሃሴ', 'ነሃሴ'),
    ]
    DAY_CHOICES = [
        ('ሠኞ','ሠኞ'),
        ('ማግሠኞ','ማግሠኞ'),
        ('ረቡዕ','ረቡዕ'),
        ('ሓሙስ','ሓሙስ'),
        ('ዓርብ','ዓርብ'),
        ('ቅዳሜ','ቅዳሜ'),
        ('እሑድ','እሑድ'),

    ]
    day = forms.ChoiceField(choices=DAY_CHOICES,label='የጦርነቱ ቀን፡')
    war_month = forms.ChoiceField(choices=OPTIONS,label='የጦርነቱ ወር፡')
    pregnancy_month = forms.ChoiceField(choices=OPTIONS, label="የተፀነሰበት ወር፡")
    month = forms.ChoiceField(choices=OPTIONS,label='የታመመበት ወር፡')
    year = forms.IntegerField(max_value=2017,label='የታመመበት አመት፡')
    your_name = forms.CharField(max_length=50,label='የእርስዎ ስም፡')
    your_mothers_name = forms.CharField(max_length=50,label="የእናትዎ ስም፡")
    place_name = forms.CharField(max_length=50,label='የቦታው ስም፡፡')
    husbands_name = forms.CharField(max_length=50,label='የወንዱ ስም፡')
    wifes_name = forms.CharField(max_length=50,label="የሴቲቱ ስም፡")
    your_spouse_name = forms.CharField(max_length=50,label="የባለቤትዎ ስም፡")
    patient_name = forms.CharField(max_length=50,label="የበሽተኛው ስም፡")
    patient_mother_name = forms.CharField(max_length=50,label="የበሽተኛው እናት ስም፡")
    sick_month = forms.CharField(max_length=20,label='የታመመበት ወር፡')
    servant_name = forms.CharField(max_length=50,label='የሰራተኛው ስም፡')
    wengelawi = forms.CharField(max_length=50,label='የወንጌላዊው ስም፡')
    judge_name = forms.CharField(max_length=50,label='የዳኛው ስም፡')
    opponent_name = forms.CharField(max_length=50,label='የተሟጋች ስም፡')
    enemy_name = forms.CharField(max_length=50,label='የጠላትዎ ስም፡')
    day_name = forms.CharField(max_length=20,label='የፍርዱ ቀን፡')
    lelit = forms.CharField(max_length=50,label='የሌሊቱ ስም፡')#ሃሳበ ክርክር
    ilet = forms.CharField(max_length=20,label='የክርክሩ ቀን፡')#ሃሳበ ክርክር
class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields  = ['username', 'password', 'password_confirm']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        # Check if the passwords match
        if password != password_confirm:
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data