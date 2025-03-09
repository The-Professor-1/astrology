from django.shortcuts import render,redirect # type: ignore
from django.contrib.auth import authenticate, login, logout # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.contrib.auth.mixins import LoginRequiredMixin # type: ignore
from django.views import View # type: ignore
from django.contrib.auth.models import User # type: ignore
from .forms import RegisterForm
from home.models import User
from contactus.models import Message
from calculator.models import Users,Message_After_Transaction
# Create your views here.
def blogs(request):
    return render(request,'blog/blog.html')
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            email = form.cleaned_data.get("email")
            user = User.objects.create_user(username=username,email=email, password=password)
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'blog/register.html', {'form':form})


def login_view(request):
    error_message = None 
    if request.method == "POST":  
        username = request.POST.get("username")  
        password = request.POST.get("password")  
        user = authenticate(request, username=username, password=password)  
        if user is not None:  
            login(request, user)  
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'  
            return redirect(next_url) 
        else:
            error_message = "Invalid credentials"  
    return render(request, 'blog/login.html', {'error': error_message})

    
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect('login')
    else:
        return redirect('dashboard')

# Home View
# Using the decorator 
@login_required
def home_view(request):
    messages = Message.objects.values().order_by('-id')
    users = Users.objects.values()
    nameandnumber = Message_After_Transaction.objects.values().order_by('-id')
    user = User.objects.filter(username = request.user)
    if request.method == 'POST':
        
        if 'dashboard-user-delete' in request.POST:
            id = request.POST.get('dashboard-user-delete','')
            Users.objects.filter(id = int(id)).delete()
            users = Users.objects.values()
    return render(request, 'blog/blog.html',{'messages':messages,'users':users,'nameandnumber':nameandnumber,'user':user})
