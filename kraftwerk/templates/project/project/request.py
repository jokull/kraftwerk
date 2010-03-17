from django.conf import settings
def context(request):
    return dict(STATIC_URL=settings.STATIC_URL)
