from home.models import UserProfile

class UpdateUserStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = UserProfile.objects.filter(user=request.user).first()
            if profile:
                session_status = request.session.get('status', None)
                if session_status != profile.status:
                    request.session['status'] = profile.status
                    request.session.modified = True
        response = self.get_response(request)
        return response