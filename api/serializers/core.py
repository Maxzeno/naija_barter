from rest_framework import serializers
from api import models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        exclude = (
            'groups', 'user_permissions', 'last_login'
            )
        
        extra_kwargs = {
            'email_confirmed': {'read_only': True},
            'is_staff': {'read_only': True},
            'is_suspended': {'read_only': True},
            'is_superuser': {'read_only': True},
            'is_active': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class UserSerializerCreate(serializers.ModelSerializer):
    class Meta:
        model = models.User
        exclude = (
            'groups', 'user_permissions', 'last_login', 'created_at', 'updated_at',
            'is_active', 'is_suspended', 'is_staff', 'email_confirmed', 'is_superuser'
            )


class UserAndTokenSerializer(UserSerializer):
    token = serializers.CharField()


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Location
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        exclude = '__all__'

