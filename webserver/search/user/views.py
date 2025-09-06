# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
import json
from common_utils.jwt_utils import JWTUtils
from django.shortcuts import render
from .models import Profile


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
            persona = data.get("persona")
            expertise_level = data.get("expertise_level")

            if not all([username, email, password, persona, expertise_level]):
                return JsonResponse(
                    {
                        "error": "All fields are required (username, email, password, persona, expertise level)"
                    },
                    status=400,
                )

            VALID_PERSONAS = [
                "developer",
                "data_scientist",
                "business_analyst",
                "researcher",
                "student",
                "hr",
                "historian",
                "marketing",
                "finance",
                "designer",
                "healthcare",
                "educator",
            ]
            VALID_EXPERTISE = ["beginner", "intermediate", "expert"]

            if persona not in VALID_PERSONAS:
                return JsonResponse({"error": "Invalid persona selected"}, status=400)
            if expertise_level not in VALID_EXPERTISE:
                return JsonResponse(
                    {"error": "Invalid expertise level selected"}, status=400
                )

            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already exists"}, status=400)
            if User.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already exists"}, status=400)

            user = User.objects.create_user(
                username=username, email=email, password=password
            )

            Profile.objects.create(
                user=user, persona=persona, expertise_level=expertise_level
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
