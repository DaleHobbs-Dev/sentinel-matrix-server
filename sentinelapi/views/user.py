"""Views for User related actions."""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from rest_framework import permissions, serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response

from sentinelapi.models import Instructor

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for public user data."""

    class Meta:
        """Meta class for UserSerializer."""

        model = User
        fields = ("id", "email", "first_name", "last_name")


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for instructor registration."""

    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    profile_picture = serializers.URLField(
        required=False, allow_blank=True, allow_null=True
    )
    subject_taught = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    university = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        """Meta class for RegisterSerializer."""

        model = User
        fields = (
            "password",
            "email",
            "first_name",
            "last_name",
            "bio",
            "profile_picture",
            "subject_taught",
            "university",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_password(self, value):
        """Perform password validation using Django's built-in validators."""
        user = User(
            email=self.initial_data.get("email"),
            first_name=self.initial_data.get("first_name"),
            last_name=self.initial_data.get("last_name"),
        )
        try:
            validate_password(value, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate_email(self, value):
        """Perform case-insensitive email uniqueness validation."""
        value = User.objects.normalize_email(value).lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Create a new user and associated instructor profile."""
        instructor_data = {
            "bio": validated_data.pop("bio", None),
            "profile_picture": validated_data.pop("profile_picture", None),
            "subject_taught": validated_data.pop("subject_taught", None),
            "university": validated_data.pop("university", None),
        }
        password = validated_data.pop("password")

        with transaction.atomic():
            user = User.objects.create_user(password=password, **validated_data)
            Instructor.objects.create(user=user, **instructor_data)

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for email/password login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        """Validate email and password for login."""
        email = User.objects.normalize_email(attrs.get("email")).lower()
        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=attrs.get("password"),
        )

        if user is None:
            raise serializers.ValidationError(
                "Unable to log in with provided credentials."
            )
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")

        attrs["user"] = user
        return attrs


def _auth_response(user, http_status=status.HTTP_200_OK):
    """Return the shared auth response shape used by register and login."""
    token, _created = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "user": UserSerializer(user).data},
        status=http_status,
    )


class UserViewSet(viewsets.ViewSet):
    """ViewSet for user-related actions: register, login, and own profile."""

    queryset = User.objects.all()

    def get_permissions(self):
        """Public auth endpoints are open; everything else requires authentication."""
        if self.action in ["register_account", "user_login"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    # Custom action for registration
    @action(detail=False, methods=["post"], url_path="register")
    def register_account(self, request):
        """Register a new user account and associated instructor profile."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return _auth_response(user, status.HTTP_201_CREATED)

    # Custom action for login
    @action(detail=False, methods=["post"], url_path="login")
    def user_login(self, request):
        """Authenticate a user and return an auth token."""
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return _auth_response(serializer.validated_data["user"])

    # Custom action for retrieving the authenticated user's own profile
    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Return the authenticated user's own profile."""
        return Response(UserSerializer(request.user).data)
