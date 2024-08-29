from django.shortcuts import render
from django.shortcuts import redirect
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.csrf import csrf_protect
from .serializers import UserSerializer

from allauth.account.forms import ResetPasswordForm
from allauth.account.utils import send_email_confirmation
from allauth.account.views import LogoutView
from allauth.account.views import PasswordResetFromKeyView
from django.urls import reverse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.linkedin_oauth2.views import LinkedInOAuth2Adapter
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _

from django.core.exceptions import ValidationError
import logging
import json

from django.template import RequestContext

def custom_404(request, exception):
    response = render(request, 'Errors/404.html', {})
    response.status_code = 404
    return response

def custom_500(request, *args, **argv):
    response = render(request, 'Errors/500.html', {})
    response.status_code = 500
    return response

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
    
    
# LinkedIn

class LinkedInLogin(SocialLoginView):
    adapter_class = LinkedInOAuth2Adapter
    callback_url = settings.LINKEDIN_CALLBACK_URL
    client_class = OAuth2Client

@api_view(['GET'])
def linkedin_login(request):
    return Response({'login_url': f"{settings.BASE_URL}/accounts/linkedin_oauth2/login/"})

@api_view(['GET'])
def linkedin_callback(request):
    logger.debug(f"Callback URL: {request.build_absolute_uri()}")
    logger.debug(f"Query params: {request.GET}")

    try:
        # Use the OAuth2CallbackView directly
        adapter = LinkedInOAuth2Adapter(request)
        callback_view = OAuth2CallbackView.adapter_view(LinkedInOAuth2Adapter)
        response = callback_view(request)
        
        # If authentication is successful, create or get a token
        if request.user.is_authenticated:
            refresh = RefreshToken.for_user(request.user)
            return redirect(f"{settings.FRONTEND_URL}/Principal/main")
        else:
            return redirect(f"{settings.FRONTEND_URL}/login-failed")
    except Exception as e:
        logger.error(f"Unexpected error during LinkedIn callback: {str(e)}", exc_info=True)
        return redirect(f"{settings.FRONTEND_URL}/login-error")


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

class CustomRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                return Response({
                    "user": UserSerializer(user, context=self.get_serializer_context()).data,
                    "message": "User Created Successfully. Now perform Login to get your token",
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_context(self):
        return {"request": self.request}

@method_decorator(csrf_protect, name='dispatch')
class CustomLogoutView(LogoutView):
    def post(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            self.logout()
            return JsonResponse({
                'success': True,
                'message': 'Logout exitoso'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No hay usuario autenticado'
            }, status=400)

    def logout(self):
        auth_logout(self.request)

class CustomPasswordResetFromKeyView(APIView):
    def post(self, request, uidb36, key):
        password1 = request.data.get('new_password1')
        password2 = request.data.get('new_password2')

        if not password1 or not password2:
            return Response({
                'error': _('Missing required fields')
            }, status=status.HTTP_400_BAD_REQUEST)

        if password1 != password2:
            return Response({
                'error': _('Passwords do not match')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Crear una solicitud simulada para allauth
        dummy_request = HttpRequest()
        dummy_request.method = 'POST'
        dummy_request.POST = request.data
        dummy_request.META = request.META

        # Construir la URL completa
        full_path = reverse('account_reset_password_from_key', kwargs={'uidb36': uidb36, 'key': key})
        dummy_request.path = full_path

        # Usar la vista de allauth para procesar el restablecimiento
        view = PasswordResetFromKeyView.as_view()
        response = view(dummy_request, uidb36=uidb36, key=key)
        
        print(response)

        if response.status_code == 200:  # Redirección exitosa
            return Response({
                'success': True,
                'message': _('Password reset successfully')
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': _('Invalid or expired reset key')
            }, status=status.HTTP_400_BAD_REQUEST)        

# Validacion de Session
@require_http_methods(["GET"])
def auth_status(request):
    return JsonResponse({
        'is_authenticated': request.user.is_authenticated
    })
        
@login_required
@require_http_methods(["GET"])
def user_profile(request):
    user = request.user
    return JsonResponse({
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'profile_picture': user.profile.picture_url if hasattr(user, 'profile') else None,
        # Añade más campos según sea necesario
    })

@login_required
@require_http_methods(["GET"])
def user_detail(request):
    user = request.user
    return JsonResponse({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'is_active': user.is_active,
        'date_joined': user.date_joined.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'profile_picture': user.profile.picture_url if hasattr(user, 'profile') else None,
        # Añadir cualquier otro campo que se necesite
    })
    
# vista para actualziar perfil
@login_required
@csrf_protect
@require_http_methods(["PUT"])
def update_profile(request):
    user = request.user
    data = json.loads(request.body)
    
    # Actualiza los campos del usuario
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.email = data.get('email', user.email)
    
    try:
        user.full_clean()  # Valida los campos del usuario
        user.save()
        return JsonResponse({'message': 'El Perfil se ha actualizado'})
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)

# vista para cambiar contraseña
@login_required
@csrf_protect
@require_http_methods(["POST"])
def change_password(request):
    user = request.user
    data = json.loads(request.body)
    
    form = PasswordChangeForm(user, data)
    if form.is_valid():
        user = form.save()
        # Actualiza la sesión para que el usuario no sea desconectado
        update_session_auth_hash(request, user)
        return JsonResponse({'message': 'Contraseña modificada correctamente'})
    else:
        errors = {field: error.get_json_data() for field, error in form.errors.items()}
        return JsonResponse({'error': errors}, status=400)