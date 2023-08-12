import logging
import datetime

logger = logging.getLogger("engfrosh_site.asgi")


class LoggingMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        date = str(datetime.datetime.now())
        logger.info("%s - %s - %s - %s - %s", date, str(request.user), request.method,
                    request.path, str(response.status_code))
        return response
