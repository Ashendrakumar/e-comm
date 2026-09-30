from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


def email_taken(email, exclude_pk=None):
    return User.objects.filter(email__iexact=email).exclude(pk=exclude_pk).exists()


def unique_username(email):
    """A username derived from the email (the app signs in with email)."""
    base = email.lower()[:140]
    name, n = base, 1
    while User.objects.filter(username__iexact=name).exists():
        name, n = f'{base}-{n}', n + 1
    return name


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'username', 'date_joined']
        extra_kwargs = {'email': {'required': True, 'allow_blank': False}}

    def validate_email(self, value):
        value = User.objects.normalize_email(value)
        if email_taken(value, exclude_pk=self.instance.pk if self.instance else None):
            raise serializers.ValidationError('An account with this email already exists.')
        return value


class RegisterSerializer(serializers.Serializer):
    email      = serializers.EmailField(max_length=254)
    password   = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name  = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_email(self, value):
        value = User.objects.normalize_email(value)
        if email_taken(value):
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate(self, attrs):
        candidate = User(email=attrs['email'], first_name=attrs.get('first_name', ''),
                         last_name=attrs.get('last_name', ''))
        try:
            password_validation.validate_password(attrs['password'], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, data):
        return User.objects.create_user(
            username=unique_username(data['email']), email=data['email'], password=data['password'],
            first_name=data.get('first_name', ''), last_name=data.get('last_name', ''))


class NewPasswordMixin:
    """Validates `new_password` against AUTH_PASSWORD_VALIDATORS for `self.password_user()`."""

    def validate_new_password(self, value):
        try:
            password_validation.validate_password(value, user=self.password_user())
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value


class ChangePasswordSerializer(NewPasswordMixin, serializers.Serializer):
    old_password = serializers.CharField(trim_whitespace=False)
    new_password = serializers.CharField(trim_whitespace=False, max_length=128)

    def password_user(self):
        return self.context['request'].user

    def validate_old_password(self, value):
        if not self.password_user().check_password(value):
            raise serializers.ValidationError('Your current password is incorrect.')
        return value


class PasswordResetConfirmSerializer(NewPasswordMixin, serializers.Serializer):
    uid          = serializers.CharField()
    token        = serializers.CharField()
    new_password = serializers.CharField(trim_whitespace=False, max_length=128)

    def password_user(self):
        return self.context.get('user')
