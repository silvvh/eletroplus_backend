from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import ContactMessage
from .serializers import (
    ContactMessageSerializer,
    ContactMessageCreateSerializer,
    ContactMessageDetailSerializer
)


# Create your views here.


class ContactMessageViewSet(viewsets.ModelViewSet):
    """ViewSet para Mensagem de Contato"""
    queryset = ContactMessage.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_read', 'email']
    search_fields = ['name', 'email', 'subject', 'message']
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna serializer apropriado baseado na ação"""
        if self.action == 'create':
            return ContactMessageCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return ContactMessageDetailSerializer
        return ContactMessageSerializer
    
    def get_permissions(self):
        """Permissões específicas por ação"""
        if self.action == 'create':
            # Qualquer um pode criar mensagem de contato
            return [AllowAny()]
        elif self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            # Apenas admin pode ver/editar/deletar
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Cria mensagem de contato"""
        serializer.save()
        
        # Opcional: Enviar email de confirmação
        # self.send_confirmation_email(serializer.instance)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Marca mensagem como lida"""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Apenas administradores podem marcar mensagens como lidas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message = self.get_object()
        message.mark_as_read()
        
        serializer = self.get_serializer(message)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_replied(self, request, pk=None):
        """Marca mensagem como respondida"""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Apenas administradores podem marcar mensagens como respondidas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message = self.get_object()
        message.mark_as_replied()
        
        serializer = self.get_serializer(message)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Retorna mensagens não lidas"""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Apenas administradores podem ver mensagens não lidas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = self.get_queryset().filter(is_read=False)
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estatísticas das mensagens"""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Apenas administradores podem ver estatísticas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        total = ContactMessage.objects.count()
        unread = ContactMessage.objects.filter(is_read=False).count()
        read = ContactMessage.objects.filter(is_read=True).count()
        replied = ContactMessage.objects.exclude(replied_at=None).count()
        
        return Response({
            'total': total,
            'unread': unread,
            'read': read,
            'replied': replied,
            'pending_reply': read - replied
        })
