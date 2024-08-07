from channels.db import database_sync_to_async
from django.contrib.auth.models import User, AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        if b'authorization' in headers:
            token_name, token_key = headers[b'authorization'].decode().split()
            if token_name == 'Bearer':
                try:
                    access_token = AccessToken(token_key)
                    user_id = access_token['user_id']
                    scope['user'] = await database_sync_to_async(User.objects.get)(id=user_id)
                except Exception:
                    scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()
        return await self.inner(scope, receive, send)
    

class CertificateAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if 'ssl' in scope:
            ssl_info = scope['ssl']
            if settings.verify_certificate(ssl_info):
                scope['robot'] = True
            else:
                scope['robot'] = False
        return await self.inner(scope, receive, send)
    

