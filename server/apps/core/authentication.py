"""
JWT Authentication implementation for Django REST Framework.
"""

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

User = get_user_model()


class JWTAuthentication(authentication.BaseAuthentication):
    """
    JWT Authentication class for DRF.
    
    Expected header format:
        Authorization: Bearer <token>
    """
    
    keyword = "Bearer"
    
    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).split()
        
        if not auth_header or auth_header[0].lower() != self.keyword.lower().encode():
            return None
        
        if len(auth_header) == 1:
            msg = "Invalid token header. No credentials provided."
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth_header) > 2:
            msg = "Invalid token header. Token string should not contain spaces."
            raise exceptions.AuthenticationFailed(msg)
        
        try:
            token = auth_header[1].decode("utf-8")
        except UnicodeError:
            msg = "Invalid token header. Token string should not contain invalid characters."
            raise exceptions.AuthenticationFailed(msg)
        
        return self.authenticate_credentials(token)
    
    def authenticate_credentials(self, token):
        """
        Validate the JWT token and return the user.
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid token.")
        
        try:
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found or inactive.")
        
        return (user, token)
    
    def authenticate_header(self, request):
        return self.keyword


def generate_access_token(user):
    """
    Generate a JWT access token for the user.
    """
    from datetime import datetime, timedelta
    
    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME),
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def generate_refresh_token(user):
    """
    Generate a JWT refresh token for the user.
    """
    from datetime import datetime, timedelta
    
    payload = {
        "user_id": str(user.id),
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_REFRESH_TOKEN_LIFETIME),
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token):
    """
    Decode a JWT token without verification.
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.InvalidTokenError:
        return None
