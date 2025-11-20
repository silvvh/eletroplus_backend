from django.shortcuts import render
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth import get_user_model
from .models import ShippingAddress
from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    CustomTokenObtainPairSerializer,
    ShippingAddressSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para Usuário"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Retorna o usuário autenticado"""
        return self.request.user
    
    def get_queryset(self):
        """Retorna apenas o próprio usuário"""
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Retorna ou atualiza dados do usuário autenticado"""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=UserRegisterSerializer,
    responses={201: UserSerializer},
    examples=[
        OpenApiExample(
            'Exemplo de Registro',
            value={
                'email': 'usuario@example.com',
                'name': 'João Silva',
                'phone': '21999999999',
                'password': 'senhaSegura123',
                'password_confirm': 'senhaSegura123',
                'street': 'Rua das Flores',
                'city': 'Rio de Janeiro',
                'state': 'RJ',
                'zip_code': '20000-000',
                'country': 'Brasil',
                'birth_date': '1990-01-01',
                'cpf': '12345678900'
            },
            request_only=True
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """View para registro de novo usuário"""
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Gera token JWT para o novo usuário
        token_serializer = CustomTokenObtainPairSerializer()
        token = token_serializer.get_token(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(token.access_token),
            'refresh': str(token)
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """View customizada para login JWT"""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]  # Login também deve ser público


class ShippingAddressViewSet(viewsets.ModelViewSet):
    """ViewSet para Endereços de Entrega"""
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retorna apenas endereços do usuário autenticado"""
        return ShippingAddress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Cria endereço associado ao usuário"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Define endereço como padrão"""
        address = self.get_object()
        address.is_default = True
        address.save()
        
        serializer = self.get_serializer(address)
        return Response(serializer.data)
