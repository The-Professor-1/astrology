from django import forms  # type: ignore
from django.contrib.auth.models import User  # type: ignore

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
        ('ሠኞ', 'ሠኞ'),
        ('ማግሠኞ', 'ማግሠኞ'),
        ('ረቡዕ', 'ረቡዕ'),
        ('ሓሙስ', 'ሓሙስ'),
        ('ዓርብ', 'ዓርብ'),
        ('ቅዳሜ', 'ቅዳሜ'),
        ('እሑድ', 'እሑድ'),
    ]

    # Fields with placeholders
    day = forms.ChoiceField(
        choices=DAY_CHOICES,
        label='የጦርነቱ ቀን፡',
        widget=forms.Select(attrs={'placeholder': 'የጦርነቱ ቀን'})
    )
    war_month = forms.ChoiceField(
        choices=OPTIONS,
        label='የጦርነቱ ወር፡',
        widget=forms.Select(attrs={'placeholder': 'የጦርነቱ ወር'})
    )
    pregnancy_month = forms.ChoiceField(
        choices=OPTIONS,
        label="የተፀነሰበት ወር፡",
        widget=forms.Select(attrs={'placeholder': 'የተፀነሰበት ወር'})
    )
    month = forms.ChoiceField(
        choices=OPTIONS,
        label='የታመመበት ወር፡',
        widget=forms.Select(attrs={'placeholder': 'የታመመበት ወር'})
    )
    year = forms.IntegerField(
        max_value=2017,
        label='የታመመበት አመት፡',
        widget=forms.NumberInput(attrs={'placeholder': 'የታመመበት አመት'})
    )
    your_name = forms.CharField(
        max_length=50,
        label='የእርስዎ ስም፡',
        widget=forms.TextInput(attrs={'placeholder': 'የእርስዎ ስም'})
    )
    your_mothers_name = forms.CharField(
        max_length=50,
        label="የእናትዎ ስም፡",
        widget=forms.TextInput(attrs={'placeholder': 'የእናትዎ ስም'})
    )
    place_name = forms.CharField(
        max_length=50,
        label='የቦታው ስም፡፡',
        widget=forms.TextInput(attrs={'placeholder': 'የቦታው ስም'})
    )
    husbands_name = forms.CharField(
        max_length=50,
        label='የወንዱ ስም፡',
        widget=forms.TextInput(attrs={'placeholder': 'የወንዱ ስም'})
    )
    wifes_name = forms.CharField(
        max_length=50,
        label="የሴቲቱ ስም፡",
        widget=forms.TextInput(attrs={'placeholder': 'የሴቲቱ ስም'})
    )
    your_spouse_name = forms.CharField(
        max_length=50,
        label="የባለቤትዎ ስም፡",
        widget=forms.TextInput(attrs={'placeholder': 'የባለቤትዎ ስም'})
    )
    patient_name = forms.CharField(
        max_length=50,
        label="የበሽተኛው ስም፡",
        widget=forms.TextInput(attrs={'placeholder': 'የበሽተኛው ስም'})
    )
    patient_mother_name = forms.CharField(
        max_length=50,
        label="የበሽተኛው እናት ስም፡",
        widget=forms.TextInput(attrs={'placeholder': 'የበሽተኛው እናት ስም'})
    )
    servant_name = forms.CharField(
        max_length=50,
        label='የሰራተኛው ስም፡',
        widget=forms.TextInput(attrs={'placeholder': 'የሰራተኛው ስም'})
    )
    wengelawi = forms.CharField(
        max_length=50,
        label='የወንጌላዊው ስም፡',
        widget=forms.TextInput(attrs={'placeholder': 'የወንጌላዊው ስም'})
    )
    judge_name = forms.CharField(
        max_length=50,
        label='የዳኛው ስም፡',
        widget=forms.TextInput(attrs={'placeholder': 'የዳኛው ስም'})
    )
    opponent_name = forms.CharField(
        max_length=50,
        label='የተሟጋች ስም፡',
        widget=forms.TextInput(attrs={'placeholder': 'የተሟጋች ስም'})
    )
    enemy_name = forms.CharField(
        max_length=50,
        label='የጠላትዎ ስም፡',
        widget=forms.TextInput(attrs={'placeholder': 'የጠላትዎ ስም'})
    )
    day_name = forms.CharField(
        max_length=20,
        label='የፍርዱ ቀን፡',
        widget=forms.TextInput(attrs={'placeholder': 'የፍርዱ ቀን'})
    )
    lelit = forms.CharField(
        max_length=50,
        label='የሌሊቱ ስም፡',
        widget=forms.TextInput(attrs={'placeholder': 'የሌሊቱ ስም'})
    )
    ilet = forms.CharField(
        max_length=20,
        label='የክርክሩ ቀን፡',
        widget=forms.TextInput(attrs={'placeholder': 'የክርክሩ ቀን'})
    )

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'password_confirm']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        # Check if the passwords match
        if password != password_confirm:
            raise forms.ValidationError("Passwords do not match!")
        
        return cleaned_data
