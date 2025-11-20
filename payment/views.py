from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Payment, PaymentStatus
from .serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentUpdateSerializer
)


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet para Pagamento"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['method', 'status', 'order']
    search_fields = ['id', 'transaction_id', 'order__id']
    ordering_fields = ['created_at', 'amount', 'paid_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retorna pagamentos do usuário ou todos se for admin"""
        queryset = Payment.objects.select_related('order', 'order__user').all()
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(order__user=self.request.user)
        
        return queryset
    
    def get_serializer_class(self):
        """Retorna serializer apropriado baseado na ação"""
        if self.action == 'create':
            return PaymentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PaymentUpdateSerializer
        return PaymentSerializer
    
    def get_permissions(self):
        """Permissões específicas por ação"""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def my_payments(self, request):
        """Retorna pagamentos do usuário autenticado"""
        payments = self.get_queryset().filter(order__user=request.user)
        
        page = self.paginate_queryset(payments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        """Marca pagamento como pago"""
        payment = self.get_object()
        
        if not request.user.is_staff:
            return Response(
                {'detail': 'Apenas administradores podem marcar pagamentos como pago.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if payment.mark_as_paid():
            serializer = self.get_serializer(payment)
            return Response(serializer.data)
        
        return Response(
            {'detail': 'Não é possível marcar este pagamento como pago.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def mark_as_failed(self, request, pk=None):
        """Marca pagamento como falhou"""
        payment = self.get_object()
        
        if not request.user.is_staff:
            return Response(
                {'detail': 'Apenas administradores podem marcar pagamentos como falhou.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if payment.mark_as_failed():
            serializer = self.get_serializer(payment)
            return Response(serializer.data)
        
        return Response(
            {'detail': 'Não é possível marcar este pagamento como falhou.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def mark_as_refunded(self, request, pk=None):
        """Marca pagamento como reembolsado"""
        payment = self.get_object()
        
        if not request.user.is_staff:
            return Response(
                {'detail': 'Apenas administradores podem marcar pagamentos como reembolsado.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if payment.mark_as_refunded():
            serializer = self.get_serializer(payment)
            return Response(serializer.data)
        
        return Response(
            {'detail': 'Não é possível marcar este pagamento como reembolsado.'},
            status=status.HTTP_400_BAD_REQUEST
        )
