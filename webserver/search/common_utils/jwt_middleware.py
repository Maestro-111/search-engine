# jwt_middleware.py
from django.http import JsonResponse
from django.contrib.auth.models import User, AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from .jwt_utils import JWTUtils


class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):

        skip_paths = [
            "/auth/login",
            "/auth/refresh",
            "/auth/register",
            "/auth/user/profile",
        ]

        request_path = request.path.rstrip("/")

        if any(request_path == path for path in skip_paths):
            request.user = AnonymousUser()
            return None

        auth_header = request.META.get("HTTP_AUTHORIZATION")

        if not auth_header:
            request.user = AnonymousUser()
            return None

        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return JsonResponse(
                {"error": "Invalid authorization header format"}, status=401
            )

        payload = JWTUtils.decode_token(token)

        if "error" in payload:
            return JsonResponse({"error": payload["error"]}, status=401)

        if payload.get("type") != "access":
            return JsonResponse({"error": "Invalid token type"}, status=401)

        try:
            user = User.objects.get(id=payload["user_id"])
            request.user = user  # ✅ real User, so `is_authenticated == True`
        except User.DoesNotExist:
            request.user = AnonymousUser()

        return None
