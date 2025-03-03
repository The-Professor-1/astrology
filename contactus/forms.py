from django import forms # type: ignore
from .models import Message

class Contactus(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['name','email','message']