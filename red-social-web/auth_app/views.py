from django.shortcuts import render
from django.shortcuts import redirect
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
import logging
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
from .serializers import UserSerializer

from allauth.account.forms import ResetPasswordForm
from allauth.account.utils import send_email_confirmation
from django.utils.translation import gettext as _


from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny, IsAuthenticated

# Logger
logger = logging.getLogger(__name__)

User = get_user_model()

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        return Response(data)

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_CALLBACK_URL
    client_class = OAuth2Client

@api_view(['GET'])
def google_login(request):
    return Response({'login_url': f"{settings.BASE_URL}/accounts/google/login/"})

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user has successfully authenticated via a social provider.
        """
        # Check if email is verified
        if sociallogin.account.extra_data.get('verified_email') is False:
            msg = 'The email is not verified'
            return Response({'error': msg}, status=400)

        # Check if user exists
        try:
            user = User.objects.get(email=sociallogin.account.extra_data.get('email'))
        except User.DoesNotExist:
            # Create a new user
            user = User(
                email=sociallogin.account.extra_data.get('email'),
                username=sociallogin.account.extra_data.get('email').split('@')[0],
                first_name=sociallogin.account.extra_data.get('given_name'),
                last_name=sociallogin.account.extra_data.get('family_name'),
            )
            user.save()

            # Connect the social account to the new user
            sociallogin.connect(request, user)

@api_view(['GET'])
def google_callback(request):
    logger.debug(f"Callback URL: {request.build_absolute_uri()}")
    logger.debug(f"Query params: {request.GET}")

    try:
        # Use the OAuth2CallbackView directly
        adapter = GoogleOAuth2Adapter(request)
        callback_view = OAuth2CallbackView.adapter_view(GoogleOAuth2Adapter)
        response = callback_view(request)
        
        # If authentication is successful, create or get a token
        if request.user.is_authenticated:
            refresh = RefreshToken.for_user(request.user)
            return redirect(f"{settings.FRONTEND_URL}/Principal/main")
        else:
            return redirect(f"{settings.FRONTEND_URL}/login-failed")
    except Exception as e:
        logger.error(f"Unexpected error during Google callback: {str(e)}", exc_info=True)
        return redirect(f"{settings.FRONTEND_URL}/login-error")


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFToken(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"detail": "CSRF cookie set"})

class LoginView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if email is None or password is None:
            return Response({'error': 'Please provide both email and password'},
                            status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                serializer = UserSerializer(user)
                return Response({
                    "user": serializer.data,
                    "detail": "Successfully logged in."
                })
            else:
                return Response({"detail": "User account is disabled."},
                                status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"detail": "Invalid credentials."},
                            status=status.HTTP_401_UNAUTHORIZED)

class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': _('Email is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.filter(email=email).first()
        if user:
            # Se usa el formulario de ResetPasswordForm de allauth
            form = ResetPasswordForm({'email': email})
            if form.is_valid():
                form.save(request)
                return Response(
                    {'message': _('Password reset e-mail has been sent.')},
                    status=status.HTTP_200_OK
                )
        else:
            # Si el usuario no existe, enviamos una respuesta genérica por seguridad
            return Response(
                {'message': _('If a user with this email exists, a password reset email will be sent.')},
                status=status.HTTP_200_OK
            )

        return Response(
            {'error': _('An error occurred. Please try again.')},
            status=status.HTTP_400_BAD_REQUEST
        )