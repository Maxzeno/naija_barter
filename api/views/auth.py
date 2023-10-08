from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, mixins, views
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from rest_framework_simplejwt.exceptions import InvalidToken

from decouple import config


from rest_framework.permissions import IsAuthenticated, BasePermission
from drf_spectacular.utils import extend_schema

from rest_framework_simplejwt.views import (
    TokenObtainPairView
)
from api import serializers
from api.serializers.auth import ChangePasswordSerializer
from api.serializers.core import UserSerializer
from api.utils.custom_status_code import HTTP_450_EMAIL_NOT_CONFIRMED


class NoPatchPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method == "PATCH":
            return False
        return True


class UpdateOnlyAPIView(mixins.UpdateModelMixin,
                        generics.GenericAPIView):
    """
    Concrete view for updating a model instance.
    """

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


@extend_schema(tags=['Auth'], responses=serializers.UserAndTokenSerializer)
class MyTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '').strip()
        user = get_user_model().objects.filter(email=email).first()
        if not user:
            raise InvalidToken()

        if not user.is_active:
            return Response({'detail': "user is not active"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()
        access_token = serializer.validated_data.get('access')
        if access_token is None:
            raise InvalidToken()

        user_serializer = UserSerializer(user)
        data = user_serializer.data

        if not user.email_confirmed:
            return Response({'detail': "Email not confirmed"}, status=HTTP_450_EMAIL_NOT_CONFIRMED)

        data['token'] = access_token
        print(data)

        return Response(data, status=status.HTTP_200_OK)


# @extend_schema(tags=['Auth'])
# class MyTokenRefreshView(TokenRefreshView):
# 	pass


# @extend_schema(tags=['Auth'])
# class MyTokenVerifyView(TokenVerifyView):
# 	pass


# @extend_schema(tags=['Auth'])
# class MyTokenBlacklistView(TokenBlacklistView):
# 	pass


@extend_schema(tags=['Auth'], responses=serializers.UserAndTokenSerializer)
class UserView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = serializers.UserSerializer(request.user)
        data = serializer.data
        data['token'] = request.META.get('HTTP_AUTHORIZATION', '').split()[-1]
        return Response(data)


@extend_schema(tags=['Auth'])
class ForgotPasswordView(generics.CreateAPIView):
    serializer_class = serializers.ForgotPasswordSerializer
    authentication_classes = ()
    permission_classes = ()

    def create(self, request, *args, **kwargs):
        email = request.data.get('email', '').strip()
        user = get_user_model().objects.filter(email=email).first()

        if user:
            # html_body = get_template('login/template_confirm_email.html').render({'confirmation_email': link, 'base_url': base_url})
            try:
                msg = EmailMultiAlternatives(
                    'Password Reset OTP Code',
                    f'OTP code use it to confirm your email: {user.generate_otp()}',
                    config('EMAIL_HOST_USER'),
                    [email]
                )
                # msg.attach_alternative(html_body, "text/html")
                msg.send()
                return Response({'detail': 'If an account with this email exists, a password reset email has been sent.'}, status=status.HTTP_200_OK)
            except ConnectionRefusedError as e:
                return Response({'detail': 'An error accurred while tring to send email'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'detail': 'If an account with this email exists, a password reset email has been sent.'}, status=status.HTTP_200_OK)


@extend_schema(tags=['Auth'])
class VerifyOTP(generics.CreateAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = serializers.VerifyOTPSerializer

    def create(self, request):
        email = request.data.get('email', '').strip()
        opt = request.data.get('otp', '').strip()
        user = get_object_or_404(get_user_model(), email=email)
        status_code = status.HTTP_404_NOT_FOUND
        data = {'detail': "OTP is Invalid"}
        if user.verify_otp(opt):
            data['detail'] = "OTP Valid"
            status_code = status.HTTP_200_OK
        return Response(data, status=status_code)


@extend_schema(tags=['Auth'])
class PasswordResetView(UpdateOnlyAPIView):
    serializer_class = serializers.PasswordResetSerializer
    authentication_classes = ()
    permission_classes = ()

    def update(self, request, *args, **kwargs):
        email = request.data.get('email', '').strip()
        opt = request.data.get('otp', '').strip()
        user = get_object_or_404(get_user_model(), email=email)

        if user and user.verify_otp(opt):
            password = request.data.get('password', '').strip()
            password_again = request.data.get('password_again', '').strip()
            try:
                password_validation.validate_password(password)
            except ValidationError as e:
                return Response({'detail': e.messages[-1]}, status=status.HTTP_400_BAD_REQUEST)
            if password != password_again:
                return Response({'detail': 'password and repeat does not match'}, status=status.HTTP_400_BAD_REQUEST)
            user.clear_otp()
            user.password = password
            user.save()

            return Response({'detail': 'Password reset successful'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid token or user'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Auth'])
class ConfirmEmailView(generics.CreateAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = serializers.VerifyOTPSerializer

    def create(self, request):
        email = request.data.get('email', '').strip()
        opt = request.data.get('otp', '').strip()
        user = get_object_or_404(get_user_model(), email=email)
        status_code = status.HTTP_404_NOT_FOUND
        data = {'detail': "User or OTP invalid"}
        if user.verify_otp(opt):
            data['detail'] = "User email confirmed"
            user.email_confirmed = True
            user.clear_otp()
            user.save()
            status_code = status.HTTP_200_OK
        return Response(data, status=status_code)


@extend_schema(tags=['Auth'])
class SendConfirmEmailView(generics.CreateAPIView):
    serializer_class = serializers.ForgotPasswordSerializer
    authentication_classes = ()
    permission_classes = ()

    def create(self, request, *args, **kwargs):
        email = request.data.get('email', '').strip()
        user = get_user_model().objects.filter(email=email).first()

        if user:
            # html_body = get_template('login/template_confirm_email.html').render({'confirmation_email': link, 'base_url': base_url})
            try:
                msg = EmailMultiAlternatives(
                    'Confirm Your Email Code',
                    f'OTP code use it to confirm your email: {user.generate_otp()}',
                    config('EMAIL_HOST_USER'),
                    [email]
                )
                # msg.attach_alternative(html_body, "text/html")
                msg.send()
                return Response({'detail': 'If an account with this email exists, a confirmation email has been sent.'}, status=status.HTTP_200_OK)
            except ConnectionRefusedError as e:
                return Response({'detail': 'An error accurred while tring to send email'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'detail': 'If an account with this email exists, a confirmation  email has been sent.'}, status=status.HTTP_200_OK)


@extend_schema(tags=['Auth'], responses=serializers.MessageSerializer)
class ChangePasswordView(generics.GenericAPIView):
    serializer_class = serializers.ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid()
        user = get_user_model().objects.filter(pk=request.user.id).first()
        old_password = serializer.validated_data.get('old_password')
        new_password = serializer.validated_data.get('new_password')
        new_password_again = serializer.validated_data.get(
            'new_password_again')
        if not user.check_password(old_password):
            return Response({'detail': 'Invalid Password'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            password_validation.validate_password(new_password)
        except ValidationError as e:
            return Response({'detail': e}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != new_password_again:
            return Response({'detail': 'Password and repeat does not match'}, status=status.HTTP_400_BAD_REQUEST)
        user.password = new_password
        user.save()
        return Response({'detail': 'Password changed'}, status=status.HTTP_200_OK)
