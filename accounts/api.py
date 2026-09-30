"""Customer account endpoints under /api/v1/auth/ (mobile app).

Token auth: sign-up / sign-in return {"token", "user"}; send the token on every
later request as `Authorization: Token <token>`. One token per account, shared by
the user's devices — signing out, changing or resetting the password revokes it.

    POST /auth/register/                 {email, password, first_name?, last_name?}
    POST /auth/login/                    {login (email or username), password}
    POST /auth/logout/                   revoke the token
    GET  /auth/me/   PATCH /auth/me/     profile {email, first_name, last_name}
    POST /auth/change-password/          {old_password, new_password} -> new token
    POST /auth/password-reset/           {email} -> emails a reset code / link
    POST /auth/password-reset/confirm/   {uid, token, new_password}
    POST /auth/delete-account/           {password} — permanently deletes the account
"""
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api_utils import rate_limited
from core.branding import get_site_name
from core.notifications import send_email
from .serializers import (ChangePasswordSerializer, PasswordResetConfirmSerializer,
                          RegisterSerializer, UserSerializer)


def auth_response(user, request, code=status.HTTP_200_OK):
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key,
                     'user': UserSerializer(user, context={'request': request}).data}, status=code)


def revoke_tokens(user):
    Token.objects.filter(user=user).delete()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        limited = rate_limited(request, 'register')
        if limited:
            return limited
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return auth_response(serializer.save(), request, code=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        limited = rate_limited(request, 'api-login', settings.RATELIMIT_LOGIN)
        if limited:
            return limited
        login    = str(request.data.get('login') or request.data.get('email') or
                       request.data.get('username') or '').strip()
        password = str(request.data.get('password') or '')
        if not login or not password:
            return Response({'detail': 'Enter your email and password.'}, status=status.HTTP_400_BAD_REQUEST)

        usernames = [login]
        if '@' in login:
            usernames = list(User.objects.filter(email__iexact=login).values_list('username', flat=True)) or [login]
        for username in usernames:
            user = authenticate(request, username=username, password=password)
            if user:
                return auth_response(user, request)
        return Response({'detail': 'Incorrect email or password.'}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        revoke_tokens(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = UserSerializer
    http_method_names  = ['get', 'patch', 'options', 'head']

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        limited = rate_limited(request, 'api-login', settings.RATELIMIT_LOGIN)
        if limited:
            return limited
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        revoke_tokens(user)                                 # other devices must sign in again
        return auth_response(user, request)


class PasswordResetView(APIView):
    """Always answers the same way, so it can't be used to test which emails have accounts."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        limited = rate_limited(request, 'password-reset', '5/h')
        if limited:
            return limited
        email = User.objects.normalize_email(str(request.data.get('email') or '').strip())
        if email:
            for user in User.objects.filter(email__iexact=email, is_active=True):
                if user.has_usable_password():
                    self.send_reset_email(user)
        return Response({'detail': 'If an account exists for that email, we have sent password reset '
                                   'instructions to it.'})

    @staticmethod
    def send_reset_email(user):
        uid   = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        site  = get_site_name()
        lines = [f'Hi {user.first_name or user.username},', '',
                 f'We received a request to reset your {site} password.']
        link  = settings.API_PASSWORD_RESET_URL
        if link:
            lines += ['Open this link on your phone to choose a new password:',
                      link.format(uid=uid, token=token)]
        lines += ['', 'Or enter these details in the app:', f'Reset ID: {uid}', f'Reset code: {token}', '',
                  "If you didn't ask for this, you can ignore this email — your password is unchanged."]
        send_email(EmailMessage(subject=f'Reset your {site} password', body='\n'.join(lines),
                                from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email]))


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        limited = rate_limited(request, 'password-reset-confirm')
        if limited:
            return limited
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(str(request.data.get('uid', '')))),
                                    is_active=True)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None
        if not user or not default_token_generator.check_token(user, str(request.data.get('token', ''))):
            return Response({'detail': 'This reset code is invalid or has expired. Please request a new one.'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = PasswordResetConfirmSerializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])               # also invalidates the reset code
        revoke_tokens(user)
        return auth_response(user, request)


class DeleteAccountView(APIView):
    """Required by the app stores. The wishlist and token go with the account;
    published reviews stay, detached from it (Review.user is SET_NULL)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        limited = rate_limited(request, 'api-login', settings.RATELIMIT_LOGIN)
        if limited:
            return limited
        user = request.user
        if user.is_staff or user.is_superuser:
            return Response({'detail': 'Staff accounts cannot be deleted from the app.'},
                            status=status.HTTP_403_FORBIDDEN)
        if not user.check_password(str(request.data.get('password') or '')):
            return Response({'password': ['Your password is incorrect.']}, status=status.HTTP_400_BAD_REQUEST)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
