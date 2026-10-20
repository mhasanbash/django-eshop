import jwt
from channels.db import database_sync_to_async
from django.conf import settings
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

class JWTAuthMiddleware:
    """Authenticate WebSocket connections using JWT."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token")
        print(f"token : {token}")

        if token:
            token = token[0]  # first value
            try:
                access = await self.get_user_from_token(token)   
                print(f"access : {access}")
                user_id = access["user_id"]  # extract user_id from token payload
                user = await self.get_user(user_id)
                scope["user"] = user
                print(" JWT accept")
            except jwt.ExpiredSignatureError:
                print("❌ JWT expired")
            except jwt.InvalidTokenError:
                print("❌ Invalid JWT token")
        else:
            print("❌ No JWT token provided")

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            access = AccessToken(token)
            print(f"access in get_user_from_token : {access}")
            return access
        except Exception:
            return AnonymousUser()
        
    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()