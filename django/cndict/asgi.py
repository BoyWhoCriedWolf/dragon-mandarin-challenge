"""
ASGI config for cndict project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

# This has to come before the imports below, since they ultimately import models
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cndict.settings')
app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
import mainapp.routing

application = ProtocolTypeRouter({
    "http": app,
    "websocket": URLRouter(
        mainapp.routing.websocket_urlpatterns
    ),
})

