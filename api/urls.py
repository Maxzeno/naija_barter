from django.urls import path, include

from api import views

from rest_framework import routers

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

router = routers.DefaultRouter()

router.register('user', views.UserViewSet, basename='user')
router.register('product', views.ProductViewSet, basename='product')
router.register('location', views.LocationViewSet, basename='location')
router.register('category', views.CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('token/blacklist/', views.MyTokenBlacklistView.as_view(), name='token_blacklist'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('password-reset/<str:uid>/<str:token>/', views.PasswordResetView.as_view(), name='password_reset'),
    path('send-confirm-email/<str:uid>/', views.SendConfirmEmailView.as_view(), name='send_confirm_email'),
    path('confirm-email/<str:uid>/<str:token>/', views.ConfirmEmailView.as_view(), name='confirm_email'),
    path('user-verify/', views.UserView.as_view(), name='user'),

    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
	path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]