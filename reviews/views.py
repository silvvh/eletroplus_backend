from django.shortcuts import render
from django.db import models
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import Review
from .serializers import (
    ReviewSerializer,
    ReviewCreateSerializer,
    ReviewUpdateSerializer
)


# Create your views here.


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet para Avaliação"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'rating', 'user']
    search_fields = ['comment', 'product__name', 'user__email']
    ordering_fields = ['created_at', 'rating', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retorna todas as avaliações"""
        queryset = Review.objects.select_related('user', 'product').all()
        
        # Filtro por produto se fornecido
        product_id = self.request.query_params.get('product_id', None)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset
    
    def get_serializer_class(self):
        """Retorna serializer apropriado baseado na ação"""
        if self.action == 'create':
            return ReviewCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        return ReviewSerializer
    
    def get_permissions(self):
        """Permissões específicas por ação"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [IsAuthenticatedOrReadOnly()]
    
    def perform_create(self, serializer):
        """Cria avaliação associada ao usuário"""
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        """Atualiza apenas avaliações do próprio usuário"""
        review = self.get_object()
        
        if review.user != self.request.user and not self.request.user.is_staff:
            raise PermissionError("Você só pode editar suas próprias avaliações.")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Deleta apenas avaliações do próprio usuário"""
        if instance.user != self.request.user and not self.request.user.is_staff:
            raise PermissionError("Você só pode deletar suas próprias avaliações.")
        
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Retorna avaliações do usuário autenticado"""
        reviews = self.get_queryset().filter(user=request.user)
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Retorna avaliações de um produto específico"""
        product_id = request.query_params.get('product_id', None)
        
        if not product_id:
            return Response(
                {'detail': 'Parâmetro product_id é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviews = self.get_queryset().filter(product_id=product_id)
        
        # Estatísticas
        total_reviews = reviews.count()
        avg_rating = reviews.aggregate(
            avg=models.Avg('rating')
        )['avg'] or 0
        
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[i] = reviews.filter(rating=i).count()
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['statistics'] = {
                'total_reviews': total_reviews,
                'average_rating': round(avg_rating, 2),
                'rating_distribution': rating_distribution
            }
            return response
        
        serializer = self.get_serializer(reviews, many=True)
        return Response({
            'reviews': serializer.data,
            'statistics': {
                'total_reviews': total_reviews,
                'average_rating': round(avg_rating, 2),
                'rating_distribution': rating_distribution
            }
        })
    
    @action(detail=False, methods=['get'])
    def by_rating(self, request):
        """Retorna avaliações filtradas por rating"""
        rating = request.query_params.get('rating', None)
        
        if not rating:
            return Response(
                {'detail': 'Parâmetro rating é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                raise ValueError
        except ValueError:
            return Response(
                {'detail': 'Rating deve ser um número entre 1 e 5.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviews = self.get_queryset().filter(rating=rating)
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
