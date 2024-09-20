import threading
from django.utils.deprecation import MiddlewareMixin


class BaseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        assert hasattr(self, 'process_request'), (
            "%s must define a process_request method".format(
                self.__class__.__name__)
        )

        self.process_request(request)

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response


class CurrentMethodMiddleware(MiddlewareMixin):
    """
    Always have access to the current user
    """
    request_str = None

    def process_request(self, request):
        self.__class__.set_method(request.method.upper())

    def process_response(self, request, response):
        self.__class__.del_method()
        return response

    def process_exception(self, request, exception):
        self.__class__.del_method()

    @classmethod
    def get_method(cls, default=None):
        return cls.request_str

    @classmethod
    def set_method(cls, method):
        cls.request_str = method

    @classmethod
    def del_method(cls):
        cls.request_str = None
