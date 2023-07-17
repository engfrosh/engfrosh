from django.utils.encoding import smart_text
from rest_framework import renderers


class PassthroughRenderer(renderers.BaseRenderer):
    media_type = 'text/calendar'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        return smart_text(data, encoding=self.charset)
