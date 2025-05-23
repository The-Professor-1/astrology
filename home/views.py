from django.shortcuts import render, redirect, get_object_or_404,HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Post, PostImage, Like, Comment, Reply,UserProfile,SiteStats
from .forms import PostForm, CommentForm, ReplyForm,RegisterForm, LoginForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

def home(request):
    stats, created = SiteStats.objects.get_or_create(id=1)
    stats.home_page_visits += 1
    stats.save()
    posts = Post.objects.prefetch_related("images", "likes", "comments__replies").order_by("-created_at")
    admin = request.session.get('admin', 0)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")
        action = request.POST.get('action')
        if action == 'post_button':
            form = PostForm(request.POST)
            images = request.FILES.getlist("images")  # Get multiple images

            if form.is_valid():
                post = form.save(commit=False)
                post.user = request.user
                post.save()

                for img in images:
                    PostImage.objects.create(post=post, image=img)

                return redirect("home")

    else:
        form = PostForm()
    
    comment_form = CommentForm()

    return render(request, "home/home.html", {"form": form, "posts": posts,"home_page_visit": stats.home_page_visits, "comment_form": comment_form,'admin':admin})

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:
        like.delete()  # Unlike if already liked
        liked = False
    else:
        liked = True

    return JsonResponse({"liked": liked, "like_count": post.likes.count()})
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()

            # Return JSON response for AJAX
            return JsonResponse({
                "id": comment.id,
                "user": comment.user.username,
                "text": comment.text,
                "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
            })

    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def add_reply(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.method == "POST":
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.user = request.user
            reply.comment = comment
            reply.save()

            # Return JSON response for AJAX
            return JsonResponse({
                "id": reply.id,
                "user": reply.user.username,
                "text": reply.text,
                "created_at": reply.created_at.strftime("%Y-%m-%d %H:%M"),
                "comment_id": comment.id,
            })

    return JsonResponse({"error": "Invalid request"}, status=400)
def user_register(request):
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'register_button':
            form = RegisterForm(request.POST)
            if form.is_valid():
                try:
                    # Save the user
                    user = form.save()

                    # Check if a profile already exists
                    if not UserProfile.objects.filter(user=user).exists():
                        UserProfile.objects.create(
                            user=user,
                            status="denied"
                        )

                    messages.success(request, "Registration successful! You can now log in.")
                    return redirect("login")

                except Exception as e:
                    messages.error(request, f"Registration failed: {str(e)}")
            else:
                messages.error(request, "Registration failed. Please correct the errors below.")
        else:
            messages.error(request, "Invalid form submission.")
    else:
        form = RegisterForm()

    return render(request, "home/register.html", {"form": form})
def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        admin = 0  # Default value
        status = "denied"  # Default status

        if form.is_valid():
            username = form.cleaned_data["username"].lower()  # Convert to lowercase for case-insensitive login
            password = form.cleaned_data["password"]

            # Check if username exists
            user_exists = User.objects.filter(username=username).exists()

            # Authenticate user
            user = authenticate(request, username=username, password=password)

            if user:
                if user.is_superuser:
                    admin = 1
                
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    status = user_profile.status  
                except UserProfile.DoesNotExist:
                    status = "not_set"
                
                login(request, user)
                messages.success(request, f"Welcome, {user.username}!")
                
                request.session['admin'] = admin 
                request.session['status'] = status  
                return redirect("home")
            else:
                if user_exists:
                    messages.error(request, "Password is incorrect for this username.")
                else:
                    messages.error(request, "Username or password is incorrect.")

    else:
        form = LoginForm()

    return render(request, "home/login.html", {"form": form})

def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")
@login_required
def delete_comment(request, comment_id):
    comment = Comment.objects.get(id=comment_id)
    if request.user == comment.user or request.session.get('admin', 0) == 1:
        comment.delete()
    return redirect('home')
@login_required
def delete_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        
        # Check if the user is an admin or the post creator
        if request.user == post.user or request.session.get('admin', 0) == 1:
            post.delete()
            messages.success(request, 'Post deleted successfully.')
        else:
            messages.error(request, 'You do not have permission to delete this post.')
    
    return redirect('home')  # Redirect to the home page or wherever appropriate
@login_required
def delete_reply(request, reply_id):
    reply = Reply.objects.get(id=reply_id)
    if request.user == reply.user or request.session.get('admin', 0) == 1:
        reply.delete()
    return redirect('home')