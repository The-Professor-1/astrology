from django.shortcuts import render,redirect # type: ignore
from django.contrib.auth import authenticate, login, logout # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.contrib.auth.mixins import LoginRequiredMixin # type: ignore
from django.views import View # type: ignore
from django.contrib.auth.models import User # type: ignore
from .forms import RegisterForm
from django.shortcuts import get_object_or_404
from django.contrib import messages
from home.models import User,UserProfile
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
    messages_data = Message.objects.values().order_by('-id')
    users = Users.objects.values()
    nameandnumber = Message_After_Transaction.objects.values().order_by('-id')

    if request.method == 'POST':
        # Handle user deletion
        if 'dashboard-user-delete' in request.POST:
            user_id = request.POST.get('dashboard-user-delete', '')
            if user_id:
                try:
                    user = get_object_or_404(Users, id=int(user_id))  # Ensure the user exists
                    user.delete()
                    messages.success(request, "User deleted successfully!")
                except Exception as e:
                    messages.error(request, f"An error occurred while deleting the user: {str(e)}")

            users = Users.objects.values()  # Refresh the user list after deletion

        # Handle permission update
        if 'give_permission_buttton' in request.POST:
            username = request.POST.get('username')
            if username:
                # Update status for UserProfile and Message_After_Transaction models
                try:
                    profile = UserProfile.objects.get(username=username)
                    profile.status = 'allowed'
                    profile.save()
                    Message_After_Transaction.objects.filter(username=username).update(status='allowed')
                    messages.success(request, f"Permissions granted to {username}!")
                except Exception as e:
                    messages.error(request, f"An error occurred while updating permissions: {str(e)}")

    return render(request, 'blog/blog.html', {
        'messages': messages_data,
        'users': users,
        'nameandnumber': nameandnumber
    })
