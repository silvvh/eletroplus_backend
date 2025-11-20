from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ProductSpecification
from .serializers import (
    CategorySerializer,
    CategoryDetailSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductSpecificationSerializer
)


# Create your views here.

class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet para Categoria"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """Retorna serializer apropriado baseado na ação"""
        if self.action == 'retrieve':
            return CategoryDetailSerializer
        return CategorySerializer
    
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Retorna produtos de uma categoria"""
        category = self.get_object()
        products = category.products.all()
        
        # Filtros opcionais
        brand = request.query_params.get('brand', None)
        min_price = request.query_params.get('min_price', None)
        max_price = request.query_params.get('max_price', None)
        featured = request.query_params.get('featured', None)
        
        if brand:
            products = products.filter(brand__icontains=brand)
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        if featured:
            products = products.filter(is_featured=True)
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet para Produto"""
    queryset = Product.objects.select_related('category').prefetch_related('specifications').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'is_featured']
    search_fields = ['name', 'description', 'brand', 'model']
    ordering_fields = ['price', 'rating', 'created_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna serializer apropriado baseado na ação"""
        if self.action in ['list', 'retrieve']:
            if self.action == 'retrieve':
                return ProductDetailSerializer
            return ProductListSerializer
        return ProductCreateUpdateSerializer
    
    def get_permissions(self):
        """Permissões específicas por ação"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Retorna produtos em destaque"""
        products = self.queryset.filter(is_featured=True)
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def on_sale(self, request):
        """Retorna produtos com desconto"""
        products = self.queryset.filter(discount_price__isnull=False)
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'post'])
    def specifications(self, request, pk=None):
        """Gerencia especificações técnicas do produto"""
        product = self.get_object()
        
        if request.method == 'GET':
            specifications = product.specifications.all()
            serializer = ProductSpecificationSerializer(specifications, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            if not request.user.is_staff:
                return Response(
                    {'detail': 'Apenas administradores podem adicionar especificações.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = ProductSpecificationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(product=product)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
