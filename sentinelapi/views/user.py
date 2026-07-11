"""Views for User related actions/methods.

Methods allowed by this ViewSet:
    get_permissions   -- Allows anonymous access for register/login; requires auth for everything else.
    register_account  -- Creates a new user + Instructor profile, returns an auth token.
    user_login        -- Authenticates by email/password, returns an auth token.
    me                -- Returns the authenticated user's own profile.
"""

from django.contrib.auth import get_user_model
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from sentinelapi.serializers import UserSerializer, RegisterSerializer, LoginSerializer

# Instanciate the User model for use in serializers and views.
# Since our User model is custom we use get_user_model() to retrieve it.
User = get_user_model()


# Helper function to generate a consistent authentication response.
# Starts with underscore to indicate that it is intended for only to be used within this module.
def _auth_response(user, http_status=status.HTTP_200_OK):
    """Return the shared auth response shape used by register and login."""

    # Generate or retrieve an authentication token for the given user.
    # Returns a tuple: (token, created), where 'token' is the Token instance and
    # 'created' is a boolean indicating if the token was newly created.
    token, _created = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "user": UserSerializer(user).data},
        status=http_status,
    )


class UserViewSet(viewsets.ViewSet):
    """ViewSet for user-related actions: register, login, and own profile."""

    def get_permissions(self):
        """Public auth endpoints are open; everything else requires authentication."""
        if self.action in ["register_account", "user_login"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def register_account(self, request):
        """Register a new user account and associated instructor profile."""

        # Instantiate the serializer class with the incoming request data
        # to make a serializer object that can validate and save the data.
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return _auth_response(user, status.HTTP_201_CREATED)

    def user_login(self, request):
        """Authenticate a user and return an auth token."""
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return _auth_response(serializer.validated_data["user"])

    # Endpoint to retrieve the authenticated user's own profile.
    # Method used to make User Context available to the frontend.
    def me(self, request):
        """Return the authenticated user's own profile."""
        return Response(UserSerializer(request.user).data)
