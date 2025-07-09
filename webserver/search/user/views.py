# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
import json
from common_utils.jwt_utils import JWTUtils
from django.shortcuts import render


@csrf_exempt
def login(request):
    if request.method == "GET":
        return render(request, "user/login.html")

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")
            if not username or not password:
                return JsonResponse(
                    {"error": "Username and password required"}, status=400
                )
            user = authenticate(username=username, password=password)
            if not user:
                return JsonResponse({"error": "Invalid credentials"}, status=401)
            # Generate tokens
            tokens = JWTUtils.generate_tokens(user)
            return JsonResponse(
                {
                    "message": "Login successful",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                    **tokens,
                }
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def register(request):
    if request.method == "GET":
        return render(request, "user/register.html")

    elif request.method == "POST":
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
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                    **tokens,
                }
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


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


def profile(request):
    """Handle both HTML page requests and API requests"""

    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    auth_header = request.META.get("HTTP_AUTHORIZATION")

    if auth_header:
        try:
            token = auth_header.split(" ")[1]
            payload = JWTUtils.decode_token(token)

            if "error" in payload:
                return JsonResponse({"error": payload["error"]}, status=401)

            if payload.get("type") != "access":
                return JsonResponse({"error": "Invalid token type"}, status=401)

            user = User.objects.get(id=payload["user_id"])

            return JsonResponse(
                {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "date_joined": user.date_joined.isoformat(),
                    }
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=401)

    else:
        return render(request, "user/profile.html")
