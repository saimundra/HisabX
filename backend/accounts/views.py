from django.db import IntegrityError, transaction
from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .serializers import (
    RegisterSerializer,
    PublicUserSerializer,
    LoginSerializer,            
    ChangePasswordSerializer,
)

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                user = serializer.save()
        except IntegrityError:
            return Response({"message": "Could not create user due to a database error."},
                            status=status.HTTP_400_BAD_REQUEST)

        
        refresh = RefreshToken.for_user(user)
        public_data = PublicUserSerializer(user, context={'request': request}).data

        return Response({
            "message": "User created successfully",
            "status": True,
            "data": public_data,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh)
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
       
        data = request.data
        username = data.get("username") or data.get("email")  
        password = data.get("password")

        if not username or not password:
            return Response({"message": "Username/email and password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        
        user = authenticate(request=request, username=username, password=password)

        
        if not user and "@" in username:
            try:
                user_obj = User.objects.filter(email__iexact=username).first()
                if user_obj:
                    user = authenticate(request=request, username=getattr(user_obj, user_obj.USERNAME_FIELD), password=password)
            except Exception:
                user = None

        if not user:
            return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"message": "User account is disabled."}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": PublicUserSerializer(user, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = PublicUserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        from .serializers import UserUpdateSerializer
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"message": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  
        except Exception as e:
            return Response({"message": "Invalid or expired token.", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
