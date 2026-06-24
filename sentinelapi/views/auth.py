"""Views and serializers for authentication and authorization."""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from rest_framework import permissions, serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response

from sentinelapi.models import Instructor

User = get_user_model()


# Blueprint for creating serializer user objects
class UserSerializer(serializers.ModelSerializer):
    """Serializer for public user data."""

    # Nested configuration for the User model to specify which fields to include in the serialized output.
    class Meta:
        """Meta class for UserSerializer."""

        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


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
            "username",
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
        """Validate the password using Django's built-in validators."""
        user = User(
            username=self.initial_data.get("username"),
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
        """Ensure that the email is unique (case-insensitive)."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        """Ensure that the username is unique (case-insensitive)."""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
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

        # Use a transaction to ensure that both the User and Instructor are created together atomically.
        # If either creation fails, the transaction will be rolled back.
        with transaction.atomic():
            user = User.objects.create_user(password=password, **validated_data)
            Instructor.objects.create(user=user, **instructor_data)

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for username/password login."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        """Validate the username and password."""
        try:
            user = User.objects.get(username__iexact=attrs.get("username"))
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            raise serializers.ValidationError(
                "Unable to log in with provided credentials."
            )

        user = authenticate(
            request=self.context.get("request"),
            username=user.get_username(),
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


# module-level helper function to generate the authorization response
# utilized in both the RegisterView and LoginView classes
# accepts a user object and an optional HTTP status code (defaulting to 200 OK)
def _auth_response(user, http_status=status.HTTP_200_OK):
    """Return the shared auth response shape used by login and register."""

    token, _created = Token.objects.get_or_create(user=user)

    return Response(
        {
            "token": token.key,
            "user": UserSerializer(user).data,
        },
        status=http_status,
    )


class RegisterView(APIView):
    """Create an instructor account and return an auth token."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle POST requests to register a new user."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return _auth_response(user, status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate a user and return an auth token."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle POST requests to log in a user."""
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        return _auth_response(serializer.validated_data["user"])
