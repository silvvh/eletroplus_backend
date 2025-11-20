from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Banner
from .serializers import (
    BannerSerializer,
    BannerCreateSerializer,
    BannerUpdateSerializer
)


# Create your views here.


class BannerViewSet(viewsets.ModelViewSet):
    """ViewSet para Banner"""
    queryset = Banner.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['active']
    search_fields = ['title', 'subtitle']
    ordering_fields = ['order', 'created_at', 'updated_at']
    ordering = ['order', '-created_at']
    
    def get_serializer_class(self):
        """Retorna serializer apropriado baseado na ação"""
        if self.action == 'create':
            return BannerCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BannerUpdateSerializer
        return BannerSerializer
    
    def get_permissions(self):
        """Permissões específicas por ação"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Retorna apenas banners ativos"""
        banners = self.get_queryset().filter(active=True)
        
        page = self.paginate_queryset(banners)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(banners, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Ativa um banner"""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Apenas administradores podem ativar banners.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        banner = self.get_object()
        banner.active = True
        banner.save()
        
        serializer = self.get_serializer(banner)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Desativa um banner"""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Apenas administradores podem desativar banners.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        banner = self.get_object()
        banner.active = False
        banner.save()
        
        serializer = self.get_serializer(banner)
        return Response(serializer.data)
