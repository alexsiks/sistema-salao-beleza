from django.middleware.csrf import CsrfViewMiddleware
from .models import ActionLog

EXCLUDED_PATHS = ['/static/', '/media/', '/favicon.ico']

REPLIT_DOMAIN_PATTERNS = ['.replit.dev', '.repl.co', '.kirk.replit.dev']


class ReplicatedCsrfMiddleware(CsrfViewMiddleware):
    """
    CSRF middleware estendido que aceita automaticamente domínios Replit,
    independente da porta informada na origem.
    """
    def process_view(self, request, callback, callback_args, callback_kwargs):
        origin = request.META.get('HTTP_ORIGIN', '')
        if origin:
            # Remove scheme para verificar o host
            host_part = origin.split('://')[-1].split(':')[0]
            if any(pattern in host_part for pattern in REPLIT_DOMAIN_PATTERNS):
                return None  # Origem Replit confiável — pula verificação
        return super().process_view(request, callback, callback_args, callback_kwargs)


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
