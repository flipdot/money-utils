import base64

from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.conf import settings


def basicauth(realm):

    def fail():
        response = HttpResponse()
        response.status_code = 401
        response['WWW-Authenticate'] = 'Basic realm="{}"'.format(
            realm
        )
        return response

    def _basicauth(function):
        def wrapper(request, *args, **kwargs):
            if 'HTTP_AUTHORIZATION' in request.META:
                try:
                    method, auth = request.META['HTTP_AUTHORIZATION'].split()
                except ValueError:
                    return fail()
                if method.lower() == "basic":
                    decoded = base64.b64decode(auth).decode('utf8')
                    uname, passwd = decoded.split(':')
                    user = authenticate(username=uname, password=passwd)
                    if user is not None and user.is_active:
                        request.user = user
                        return function(request, *args, **kwargs)

            return fail()
        return wrapper
    return _basicauth
