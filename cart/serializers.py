from rest_framework import serializers
from .models import Cart, CartItem
from catalog.serializers import ProductListSerializer
from orders.serializers import CouponSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer para Item do Carrinho"""
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_id', 'quantity',
            'price_at_time', 'total_price', 'updated_at'
        ]
        read_only_fields = ['id', 'product', 'total_price', 'updated_at']
    
    def validate_quantity(self, value):
        """Valida quantidade mínima"""
        if value < 1:
            raise serializers.ValidationError("A quantidade deve ser pelo menos 1.")
        return value


class CartItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criar/atualizar item do carrinho"""
    product_id = serializers.UUIDField()
    
    class Meta:
        model = CartItem
        fields = ['product_id', 'quantity']
    
    def validate_quantity(self, value):
        """Valida quantidade mínima"""
        if value < 1:
            raise serializers.ValidationError("A quantidade deve ser pelo menos 1.")
        return value


class CartSerializer(serializers.ModelSerializer):
    """Serializer para Carrinho"""
    items = CartItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    coupon = CouponSerializer(read_only=True)
    coupon_code = serializers.CharField(source='coupon.code', read_only=True, allow_null=True)
    items_count = serializers.IntegerField(read_only=True)
    is_empty = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Cart
        fields = [
            'id', 'user_email', 'subtotal', 'total',
            'coupon', 'coupon_code', 'items', 'items_count', 'is_empty', 'updated_at'
        ]
        read_only_fields = [
            'id', 'subtotal', 'total', 'items_count', 'is_empty', 'updated_at'
        ]
