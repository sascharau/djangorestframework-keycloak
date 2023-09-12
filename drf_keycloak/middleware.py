""" Header middleware """
from django.utils.cache import add_never_cache_headers


class HeaderMiddleware:  # pylint: disable=too-few-public-methods
    """
    Security setting for the header
    """

    def __init__(self, get_response):
        """
        :param request:
        :return:
        """
        self.get_response = get_response

    def __call__(self, request):
        # modify header
        response = self.get_response(request)
        # Expires now
        response["Expires"] = 0
        # do not cache Pages/API calls
        add_never_cache_headers(response)
        # do not use X-XSS-Protection we use cps
        response["X-XSS-Protection"] = 0
        # use SSL
        response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
