from django.shortcuts import render # type: ignore
from django.http import HttpResponse # type: ignore
from .forms import Contactus
from .models import Message
from django.urls import reverse # type: ignore
# Create your views here.

def contactus(request):
    form = Contactus()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send':
            form = Contactus(data=request.POST)
            if form.is_valid():
                instance = form.save(commit=False)
                instance.foreign_key_field_id = Message.id
                instance.save()
                homepage_url = reverse('home')
                response_content = f"<h1><font color='green'>your message sent successfully!</font><br><a href='{homepage_url}'>back to home</a></h1>"
                return HttpResponse(response_content)
    return render(request,'contactus/contactus.html',{'form':form})