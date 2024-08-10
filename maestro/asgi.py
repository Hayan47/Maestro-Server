import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maestro.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from authentication.middleware import TokenAuthMiddleware, CertificateAuthMiddleware



import control.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": 
    # AllowedHostsOriginValidator(
        TokenAuthMiddleware(
            CertificateAuthMiddleware(
                URLRouter(
                    control.routing.websocket_urlpatterns
                )
            )
        # )
    ),
})
