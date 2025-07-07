# jwt_utils.py
import jwt
from datetime import datetime, timedelta
from django.conf import settings

from django.contrib.auth.models import User


class JWTUtils:
    @staticmethod
    def generate_tokens(user):
        """Generate access and refresh tokens for a user"""

        # Access token payload

        access_payload = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "exp": datetime.now() + timedelta(minutes=60),  # 1 hour
            "iat": datetime.now(),
            "type": "access",
        }

        # Refresh token payload
        refresh_payload = {
            "user_id": user.id,
            "exp": datetime.now() + timedelta(days=7),  # 7 days
            "iat": datetime.now(),
            "type": "refresh",
        }

        # Generate tokens
        access_token = jwt.encode(access_payload, settings.JWT_KEY, algorithm="HS256")
        refresh_token = jwt.encode(refresh_payload, settings.JWT_KEY, algorithm="HS256")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600,  # 1 hour in seconds
        }

    @staticmethod
    def decode_token(token):
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, settings.JWT_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}

    @staticmethod
    def refresh_access_token(refresh_token):
        """Generate new access token from refresh token"""
        try:
            payload = jwt.decode(refresh_token, settings.JWT_KEY, algorithms=["HS256"])

            if payload.get("type") != "refresh":
                return {"error": "Invalid refresh token"}

            # Get user
            user = User.objects.get(id=payload["user_id"])

            # Generate new access token
            access_payload = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "exp": datetime.now() + timedelta(minutes=60),
                "iat": datetime.now(),
                "type": "access",
            }

            access_token = jwt.encode(
                access_payload, settings.JWT_KEY, algorithm="HS256"
            )

            return {"access_token": access_token, "expires_in": 3600}

        except jwt.ExpiredSignatureError:
            return {"error": "Refresh token has expired"}
        except jwt.InvalidTokenError:
            return {"error": "Invalid refresh token"}
        except User.DoesNotExist:
            return {"error": "User not found"}
