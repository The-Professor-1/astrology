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
from calculator.models import Users,Message_After_Transaction,Allowed_Users
# Create your views here.

def login_view(request):
    error_message = None  
    if request.method == "POST": 
        action = request.POST.get("action")
        if action == 'admin_login':
            username = request.POST.get("username")  
            password = request.POST.get("password")  
            user = authenticate(request, username=username, password=password)  
            
            if user is not None:  
                login(request, user)  # Log in the user
                return redirect('blog:dashboard')  # Redirect to the correct blog page
            
            else:
                error_message = "Invalid credentials"  
                messages.error(request, error_message)  # Use Django messages framework
            
    return render(request, 'blog/admin_login.html', {'error': error_message})
    
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect('admin_login')
    else:
        return redirect('dashboard')

# Home View
# Using the decorator 
@login_required
def home_view(request):
    messages_data = Message.objects.values().order_by('-id')
    users = Users.objects.values()
    nameandnumber = Message_After_Transaction.objects.values().order_by('-id')
    allowed_users = Allowed_Users.objects.values()
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
        if 'give_permission_button' in request.POST:
            username = request.POST.get('username', '')  # Ensure the correct input field name
            if username:
                try:
                    # Update status for UserProfile
                    profile = UserProfile.objects.get(user__username=username)
                    profile.status = 'allowed'
                    profile.save()

                    # Retrieve the message(s) before deleting
                    messages_to_move = Message_After_Transaction.objects.filter(status='allowed')

                    for message in messages_to_move:
                        # Move data to Allowed_Users before deletion
                        Allowed_Users.objects.create(username=message.username, status='allowed')

                    # Delete the original records
                    messages_to_move.delete()

                    messages.success(request, f"Permissions granted to {username}, and record moved to Allowed Users!")

                except UserProfile.DoesNotExist:
                    messages.error(request, f"UserProfile for {username} does not exist.")
                except Exception as e:
                    messages.error(request, f"An error occurred while updating permissions: {str(e)}")


    return render(request, 'blog/blog.html', {
        'messages': messages_data,
        'users': users,
        'nameandnumber': nameandnumber,
        'allowed_users': allowed_users
    })
