from rest_framework import renderers


class PassthroughRenderer(renderers.BaseRenderer):
    media_type = ''
    format = ''

    def render(self, data, accepted_media_type="text/calendar", renderer_context=None):
        return data
