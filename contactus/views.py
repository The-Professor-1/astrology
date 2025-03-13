from django.shortcuts import render # type: ignore
from django.http import HttpResponse # type: ignore
from .forms import Contactus,EmailReplyForm
from django.core.mail import send_mail # type: ignore
from django.shortcuts import redirect # type: ignore
from django.contrib import messages # type: ignore
from .models import Message
from django.urls import reverse # type: ignore
# Create your views here.
def email_reply(request):
    email_to_redirected = request.GET.get('email_to', '')
    form = EmailReplyForm(initial={'email_to': email_to_redirected})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'email_reply_button':
            form = EmailReplyForm(data=request.POST)
            if form.is_valid():
                email_to = email_to_redirected
                subject = form.cleaned_data['subject']
                message = form.cleaned_data['message']
                try:
                    # Send the email
                    send_mail(
                        subject,
                        message,
                        'a1100b1100c@gmail.com',  # From email
                        [email_to],  # To email (list of recipients)
                        fail_silently=False,  # Raise error if email fails
                    )
                    messages.success(request, f"Email sent successfully to {email_to}!")
                    return redirect('some_success_page')  # Redirect after successful send
                except Exception as e:
                    messages.error(request, f"Failed to send email: {str(e)}")

    return render(request, 'contactus/email_reply.html', {'form': form,'email_to':email_to_redirected})
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