from channels.db import database_sync_to_async
from django.contrib.auth.models import User, AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings
from urllib.parse import parse_qs
import re

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if token:
            try:
                access_token = AccessToken(token)
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
        if scope['type'] == 'websocket':
            headers = dict(scope['headers'])
            client_verify = headers.get(b'x-client-verify', b'').decode()
            print(client_verify)
            client_s_dn = headers.get(b'x-client-dn', b'').decode()

            if client_verify == 'SUCCESS':
                scope['is_robot'] = True
                # You can extract more info from client_s_dn if needed
                match = re.search(r'CN=Robot(\d+)', client_s_dn)
                if match:
                    robot_id = match.group(1)
                    scope['robot_id'] = robot_id  # Store robot_id in the scope
                    print(robot_id)
                else:
                    scope['robot_id'] = None
            else:
                scope['is_robot'] = False

        return await self.inner(scope, receive, send)