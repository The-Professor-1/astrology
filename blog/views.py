from django.shortcuts import render,redirect # type: ignore
from django.contrib.auth import authenticate, login, logout # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.contrib.auth.mixins import LoginRequiredMixin # type: ignore
from django.views import View # type: ignore
from django.contrib.auth.models import User # type: ignore
from .forms import RegisterForm
from django.shortcuts import get_object_or_404,reverse
from django.contrib import messages
from home.models import User,UserProfile,SiteStats
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
    user = User.objects.values()
    users = Users.objects.values()
    userinfo = Message_After_Transaction.objects.values()
    allowed = User.objects.filter(profile__status='allowed')
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
            username = request.POST.get('give_permission_button', '')  # Ensure the correct input field name
            
            if username:
                profile = UserProfile.objects.get(user__username=username)
                if profile.status == 'allowed':
                    Message_After_Transaction.objects.filter(username=username).delete()
                    userinfo = Message_After_Transaction.objects.values()
                else:
                    try:
                        profile.status = 'allowed'
                        profile.save()
                        Message_After_Transaction.objects.filter(username=username).delete()
                        userinfo = Message_After_Transaction.objects.values()
                        messages.success(request, f"Permissions granted to {username}, and record moved to Allowed Users!")
                    except UserProfile.DoesNotExist:
                        messages.error(request, f"User {username} not found.")
                    except Message_After_Transaction.DoesNotExist:
                        messages.error(request, f"Transaction record for {username} not found.")
                    except Exception as e:
                        messages.error(request, f"An error occurred: {str(e)}")
            
            # Refresh allowed queryset after update
            allowed = User.objects.filter(profile__status='allowed')
        if 'remove_permission_button' in request.POST:
            username = request.POST.get('remove_permission_button', '')  # Ensure the correct input field name
            profile = UserProfile.objects.get(user__username=username)
            profile.status = 'denied'
            profile.save()
            Message_After_Transaction(username=username,transaction_number="second_denied",status="denied").save()
            userinfo = Message_After_Transaction.objects.values()
            Allowed_Users.objects.filter(username=username).delete()
            allowed = User.objects.filter(profile__status='allowed')
        if 'dashboard_message_delete' in request.POST:
            message_id = request.POST.get('dashboard_message_delete', '')
            if message_id:
                try:
                    message = get_object_or_404(Message, id=int(message_id))  # Ensure the message exists
                    message.delete()
                    messages.success(request, "Message deleted successfully!")
                except Exception as e:
                    messages.error(request, f"An error occurred while deleting the message: {str(e)}")
        if 'dashboard_message_reply' in request.POST:
            email_to = request.POST.get('dashboard_message_reply', '')
            return redirect(f"{reverse('contact:reply')}?email_to={email_to}")
    allowed_users = UserProfile.objects.filter(status='allowed')
    registered_users = User.objects.all()
    
    # Count directly instead of looping
    noofregistered = registered_users.count() - 2  # Subtract the two superusers
    noofallowed = allowed_users.count()
    # Ensure we fetch the first SiteStats instance
    stats = SiteStats.objects.first()

    # Ensure stats exist, fallback to 0 if not
    context = {
        "home_page_visit": stats.home_page_visits if stats else 0,
        "calculators_list_visit": stats.calculators_list_visits if stats else 0,
        "kokeb_calculator_visit": stats.kokeb_calculator_visits if stats else 0,
        "noofallowed": noofallowed,
        "noofregistered": noofregistered,
        'messages': messages_data,
        'users': users,
        'userinfo':userinfo,
        'allowed': allowed,
    }
    return render(request, 'blog/blog.html',context)
