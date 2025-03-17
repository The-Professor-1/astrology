from django.shortcuts import get_object_or_404
from home.models import UserProfile

class UpdateUserStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get the user's profile
            profile = get_object_or_404(UserProfile, user=request.user)
            # Check if session status matches database status
            session_status = request.session.get('status', None)
            if session_status != profile.status:
                # Update session with current status
                request.session['status'] = profile.status
                request.session.modified = True  # Ensure session saves
        response = self.get_response(request)
        return response