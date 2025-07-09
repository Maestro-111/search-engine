# jwt_utils.py
import jwt
from django.conf import settings
import time
from django.contrib.auth.models import User


class JWTUtils:
    @staticmethod
    def generate_tokens(user):
        """Generate access and refresh tokens for a user"""

        # Access token payload

        now = int(time.time())
        access_exp = now + (60 * 60)  # 1 hour from now
        refresh_exp = now + (7 * 24 * 60 * 60)  # 7 days from now

        access_payload = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "exp": access_exp,
            "iat": now,
            "type": "access",
        }

        # Refresh token payload
        refresh_payload = {
            "user_id": user.id,
            "exp": refresh_exp,
            "iat": now,
            "type": "refresh",
        }

        # Generate tokens
        access_token = jwt.encode(access_payload, settings.JWT_KEY, algorithm="HS256")
        refresh_token = jwt.encode(refresh_payload, settings.JWT_KEY, algorithm="HS256")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600,
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

            now = int(time.time())

            access_payload = {
                "exp": now + (60 * 60),  # 1 hour from now
                "iat": now,
                "type": "access",
            }

            user = User.objects.get(id=payload["user_id"])

            access_payload["user_id"] = user.id
            access_payload["username"] = user.username
            access_payload["email"] = user.email

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
