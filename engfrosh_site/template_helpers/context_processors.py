from django.core.cache import cache
from django.templatetags.static import static
from common_models.models import SiteImage


def background_image(request):
    url = cache.get('BACKGROUND_IMAGE_URL')
    if url is None:
        si = SiteImage.objects.filter(name="Background Image").first()
        url = si.image.url if si and si.image else static('background.png')
        cache.set('BACKGROUND_IMAGE_URL', url, 300)  # cache 5 minutes
    return {'BACKGROUND_IMAGE_URL': url}


def favicon32(request):
    url = cache.get('FAVICON_URL_32')
    if url is None:
        si = SiteImage.objects.filter(name="32x32 Favicon").first()
        url = si.image.url if si and si.image else static('favicon-32x32.png')
        cache.set('FAVICON_URL_32', url, 300)
    return {'FAVICON_URL_32': url}


def favicon16(request):
    url = cache.get('FAVICON_URL_16')
    if url is None:
        si = SiteImage.objects.filter(name="16x16 Favicon").first()
        url = si.image.url if si and si.image else static('favicon-16x16.png')
        cache.set('FAVICON_URL_16', url, 300)
    return {'FAVICON_URL_16': url}
