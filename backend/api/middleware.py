from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs


class TokenAuthMiddleware(BaseMiddleware):
    """
    Custom middleware that authenticates users via token from query string.
    """
    
    async def __call__(self, scope, receive, send):
        # Get query string from scope
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        # Extract token from query parameters
        token_key = query_params.get('token', [None])[0]
        
        if token_key:
            # Get user from token
            scope['user'] = await self.get_user_from_token(token_key)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_user_from_token(self, token_key):
        """
        Get user from authentication token.
        """
        try:
            token = Token.objects.select_related('user').get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return AnonymousUser()

