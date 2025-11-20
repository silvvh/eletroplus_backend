from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemCreateUpdateSerializer
)
from catalog.models import Product


# Create your views here.

class CartViewSet(viewsets.ModelViewSet):
    """ViewSet para Carrinho"""
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retorna apenas o carrinho do usuário autenticado"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return Cart.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Retorna ou cria o carrinho do usuário"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart
    
    def list(self, request, *args, **kwargs):
        """Retorna o carrinho do usuário"""
        return self.retrieve(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Cria carrinho (geralmente já existe, então retorna o existente)"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post', 'put', 'patch'])
    def add_item(self, request, pk=None):
        """Adiciona ou atualiza item no carrinho"""
        cart = self.get_object()
        serializer = CartItemCreateUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']
            
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {'detail': 'Produto não encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verifica estoque disponível
            available = product.available_stock
            if quantity > available:
                return Response(
                    {'detail': f'Estoque insuficiente. Disponível: {available}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Usa o preço atual do produto (ou desconto se houver)
            price_at_time = product.discount_price if product.has_discount else product.price
            
            # Cria ou atualiza o item
            cart_item, created = CartItem.objects.update_or_create(
                cart=cart,
                product=product,
                defaults={
                    'quantity': quantity,
                    'price_at_time': price_at_time
                }
            )
            
            item_serializer = CartItemSerializer(cart_item)
            return Response(
                item_serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """Remove item do carrinho"""
        cart = self.get_object()
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response(
                {'detail': 'product_id é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response(
                {'detail': 'Item não encontrado no carrinho.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """Limpa todos os itens do carrinho"""
        cart = self.get_object()
        cart.items.all().delete()
        cart.calculate_totals()
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_coupon(self, request, pk=None):
        """Atualiza código do cupom"""
        from orders.models import Coupon
        
        cart = self.get_object()
        coupon_code = request.data.get('coupon_code', '').strip().upper()
        
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                
                if not coupon.is_valid():
                    return Response(
                        {'detail': 'Cupom inválido ou expirado.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if not coupon.can_be_used():
                    return Response(
                        {'detail': 'Cupom atingiu o limite de usos.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                cart.coupon = coupon
            except Coupon.DoesNotExist:
                return Response(
                    {'detail': 'Cupom não encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            cart.coupon = None
        
        cart.save()
        cart.calculate_totals()
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
