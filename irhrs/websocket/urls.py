from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path

from irhrs.websocket.helpers import send_for_group


def index(request):
    return render(request, 'websocket/index.html', {})


def test_echo(request):
    user_id = request.GET.get('user_id', None)
    if not user_id:
        return HttpResponse("User ID is required")
    send_for_group(user_id, {'type': 'send.echo'}, msg_type='echo')
    return HttpResponse("Successfully sent the Welcome message as Echo Test")


urlpatterns = [
    path('', index),
    path('echo/', test_echo)
]
