from django.core.cache import cache
from django.templatetags.static import static
from common_models.models import SiteImage

def background_image(request):
    url = cache.get('STYLE_IMAGE_URL')
    if url is None:
        si = SiteImage.objects.filter(name="Background Image").first()
        url = si.image.url if si and si.image else static('background.png')
        cache.set('STYLE_IMAGE_URL', url, 300)  # cache 5 minutes
    return {'STYLE_IMAGE_URL': url}
