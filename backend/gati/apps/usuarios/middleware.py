from django.contrib.auth import logout
from django.utils import timezone


class SessionLimitsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now().timestamp()
            started = request.session.get("auth_started", now)
            last = request.session.get("auth_seen", now)
            if now - started >= 43200 or now - last >= 3600:
                logout(request)
            else:
                request.session["auth_started"] = started
                request.session["auth_seen"] = now
        return self.get_response(request)
