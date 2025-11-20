from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserViewSet,
    CustomTokenObtainPairView,
    ShippingAddressViewSet,
    register_user  # Importa a view separada
)

router = DefaultRouter()
# Registra apenas shipping-addresses no router
router.register(r'shipping-addresses', ShippingAddressViewSet, basename='shipping-address')

urlpatterns = [
    # Rotas de autenticação (devem vir ANTES do router)
    path('auth/register/', register_user, name='register'),  # Usa a view separada
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Rotas do UserViewSet (manuais para evitar conflito)
    path('users/me/', UserViewSet.as_view({'get': 'me', 'put': 'me', 'patch': 'me'}), name='user-me'),
    
    # Inclui rotas do router (shipping-addresses)
    path('', include(router.urls)),
]
