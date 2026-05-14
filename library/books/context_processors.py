from .models import SalonConfig


def salon_config(request):
    try:
        config = SalonConfig.get()
    except Exception:
        config = None
    return {'config': config}
