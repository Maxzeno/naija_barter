from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser

from rest_framework.viewsets import ModelViewSet
from rest_framework import filters
from drf_spectacular.utils import extend_schema
from api import serializers, models


@extend_schema(tags=['User'])
class UserViewSet(ModelViewSet):
	queryset = models.User.objects.filter(is_active=True, is_suspended=False)
	filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
	search_fields = ['name']
	ordering_fields = ['name', 'created_at']
 
	def get_serializer_class(self):
		if hasattr(self, 'action') and self.action == 'create':
			return serializers.UserSerializerCreate
		return serializers.UserSerializer
 
	def get_authenticators(self):
		if hasattr(self, 'action') and self.action == 'create':
			self.authentication_classes = []

		return [authentication_class() for authentication_class in self.authentication_classes]

	def get_permissions(self):
		if hasattr(self, 'action') and self.action == 'create':
			self.permission_classes = []

		return [permission_class() for permission_class in self.permission_classes]

	def get_parsers(self):
		self.parser_classes.append(MultiPartParser)
		return [parser_class() for parser_class in self.parser_classes]


@extend_schema(tags=['Product'])
class ProductViewSet(ModelViewSet):
	queryset = models.Product.objects.filter(is_active=True)
	serializer_class = serializers.ProductSerializer
	filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
	search_fields = ['name']
	ordering_fields = ['name', 'created_at', 'price']
	filterset_fields = ['product_type', 'category', 'location', 'user', 'exchange']
 
	def get_parsers(self):
		self.parser_classes.append(MultiPartParser)
		return [parser_class() for parser_class in self.parser_classes]



@extend_schema(tags=['Location'])
class LocationViewSet(ModelViewSet):
	queryset = models.Location.objects.all()
	serializer_class = serializers.LocationSerializer
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ['state']
	ordering_fields = ['state', 'created_at']



@extend_schema(tags=['Category'])
class CategoryViewSet(ModelViewSet):
	queryset = models.Category.objects.all()
	serializer_class = serializers.CategorySerializer
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ['name']
	ordering_fields = ['name', 'created_at']

