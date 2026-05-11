from .models import ActionLog

EXCLUDED_PATHS = ['/static/', '/media/', '/favicon.ico']


class ActionLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            skip = any(request.path.startswith(p) for p in EXCLUDED_PATHS)
            if not skip and request.method == 'POST' and response.status_code in (200, 302):
                user = request.user if request.user.is_authenticated else None
                ActionLog.log(
                    user=user,
                    action='OTHER',
                    description=f'POST {request.path}',
                    request=request,
                )
        except Exception:
            pass
        return response
