from django.core.asgi import get_asgi_application
from django.urls import path

from channels.routing import ProtocolTypeRouter, URLRouter

from irhrs.websocket.consumers import GlobalConsumer

protocol_router_config = {
    "http": get_asgi_application(),
    "websocket": URLRouter([
        path("global/", GlobalConsumer.as_asgi()),
    ]),
}

application = ProtocolTypeRouter(protocol_router_config)
