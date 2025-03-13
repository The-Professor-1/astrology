from django import forms # type: ignore
from .models import Message

class Contactus(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['name','email','message']
class EmailReplyForm(forms.Form):
    email_to = forms.EmailField()
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)