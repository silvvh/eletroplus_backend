from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from .models import Order, OrderItem, OrderStatus, Coupon
from .serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    OrderItemSerializer,
    CouponSerializer,
    CouponCreateSerializer,
    CouponUpdateSerializer,
    CouponValidateSerializer
)


# Create your views here.

class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet para Pedido"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['id']
    ordering_fields = ['created_at', 'total', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retorna pedidos do usuário ou todos se for admin"""
        queryset = Order.objects.select_related(
            'user', 'shipping_address', 'payment'
        ).prefetch_related('items__product').all()
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    def get_serializer_class(self):
        """Retorna serializer apropriado baseado na ação"""
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        elif self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderListSerializer
    
    def get_permissions(self):
        """Permissões específicas por ação"""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Cria pedido associado ao usuário"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Retorna pedidos do usuário autenticado"""
        orders = self.get_queryset().filter(user=request.user)
        
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela um pedido"""
        order = self.get_object()
        
        if not request.user.is_staff and order.user != request.user:
            return Response(
                {'detail': 'Você não tem permissão para cancelar este pedido.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELED]:
            return Response(
                {'detail': f'Não é possível cancelar um pedido com status {order.get_status_display()}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = OrderStatus.CANCELED
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)


class CouponViewSet(viewsets.ModelViewSet):
    """ViewSet para Cupom"""
    queryset = Coupon.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['active']
    search_fields = ['code']
    ordering_fields = ['created_at', 'valid_until']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna serializer apropriado baseado na ação"""
        if self.action == 'create':
            return CouponCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CouponUpdateSerializer
        return CouponSerializer
    
    def get_permissions(self):
        """Permissões específicas por ação"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """Valida um cupom e retorna informações do desconto"""
        serializer = CouponValidateSerializer(data=request.data)
        
        if serializer.is_valid():
            code = serializer.validated_data['code']
            coupon = Coupon.objects.get(code=code)
            
            response_data = {
                'code': coupon.code,
                'discount_display': coupon.get_discount_display(),
                'is_valid': coupon.is_valid(),
                'can_be_used': coupon.can_be_used(),
            }
            
            if 'amount' in serializer.validated_data:
                amount = serializer.validated_data['amount']
                discounted_amount = coupon.apply_discount(amount)
                response_data['original_amount'] = float(amount)
                response_data['discount'] = float(amount - discounted_amount)
                response_data['final_amount'] = float(discounted_amount)
            
            return Response(response_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Retorna cupons ativos e válidos"""
        from django.utils import timezone
        
        coupons = Coupon.objects.filter(
            active=True,
            valid_until__gt=timezone.now()
        ).filter(
            models.Q(current_uses__lt=models.F('max_uses'))
        )
        
        page = self.paginate_queryset(coupons)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(coupons, many=True)
        return Response(serializer.data)
