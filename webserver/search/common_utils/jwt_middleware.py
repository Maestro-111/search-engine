# jwt_middleware.py
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils.deprecation import MiddlewareMixin
from .jwt_utils import JWTUtils


class JWTAuthenticationMiddleware(MiddlewareMixin):

    def process_request(self, request):

        skip_paths = [
            "/auth/login/",
            "/auth/refresh/",
            "/auth/register/",
            "/auth/user/profile/",
        ]  # mind the path end?

        if any(request.path.startswith(path) for path in skip_paths):
            return None

        if not request.path.startswith("/auth/"):
            return None

        # Get token from Authorization header
        auth_header = request.META.get("HTTP_AUTHORIZATION")

        if not auth_header:
            return JsonResponse({"error": "Authorization header required"}, status=401)

        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return JsonResponse(
                {"error": "Invalid authorization header format"}, status=401
            )

        # Decode and validate token
        payload = JWTUtils.decode_token(token)

        if "error" in payload:
            return JsonResponse({"error": payload["error"]}, status=401)

        if payload.get("type") != "access":
            return JsonResponse({"error": "Invalid token type"}, status=401)

        try:
            user = User.objects.get(id=payload["user_id"])
            request.user = user
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=401)

        return None
