# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
import json
from common_utils.jwt_utils import JWTUtils


@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return JsonResponse({"error": "Username and password required"}, status=400)

        # Authenticate user
        user = authenticate(username=username, password=password)

        if not user:
            return JsonResponse({"error": "Invalid credentials"}, status=401)

        # Generate tokens
        tokens = JWTUtils.generate_tokens(user)

        return JsonResponse(
            {
                "message": "Login successful",
                "user": {"id": user.id, "username": user.username, "email": user.email},
                **tokens,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def refresh_token(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return JsonResponse({"error": "Refresh token required"}, status=400)

        # Refresh access token
        result = JWTUtils.refresh_access_token(refresh_token)

        if "error" in result:
            return JsonResponse({"error": result["error"]}, status=401)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not all([username, email, password]):
            return JsonResponse(
                {"error": "Username, email, and password required"}, status=400
            )

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exists"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email already exists"}, status=400)

        # Create user
        user = User.objects.create_user(
            username=username, email=email, password=password
        )

        # Generate tokens
        tokens = JWTUtils.generate_tokens(user)

        return JsonResponse(
            {
                "message": "User created successfully",
                "user": {"id": user.id, "username": user.username, "email": user.email},
                **tokens,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def profile(request):
    """Protected route - requires JWT authentication"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # User is already attached to request by middleware
    return JsonResponse(
        {
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "date_joined": request.user.date_joined.isoformat(),
            }
        }
    )
