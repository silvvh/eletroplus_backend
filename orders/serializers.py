from rest_framework import serializers
from .models import Order, OrderItem, OrderStatus
from catalog.serializers import ProductListSerializer
from users.serializers import ShippingAddressSerializer
from .models import Coupon


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer para Item do Pedido"""
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'unit_price', 'total_price', 'created_at']
        read_only_fields = ['id', 'product', 'total_price', 'created_at']
    
    def validate_quantity(self, value):
        """Valida quantidade mínima"""
        if value < 1:
            raise serializers.ValidationError("A quantidade deve ser pelo menos 1.")
        return value


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar item do pedido"""
    product_id = serializers.UUIDField()
    
    class Meta:
        model = OrderItem
        fields = ['product_id', 'quantity']
    
    def validate_quantity(self, value):
        """Valida quantidade mínima"""
        if value < 1:
            raise serializers.ValidationError("A quantidade deve ser pelo menos 1.")
        return value


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer resumido para lista de pedidos"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user_email', 'user_name', 'status', 'status_display',
            'subtotal', 'shipping', 'total', 'items_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'subtotal', 'shipping', 'total', 'items_count', 'created_at', 'updated_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para pedido"""
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = ShippingAddressSerializer(read_only=True)
    shipping_address_id = serializers.UUIDField(write_only=True, required=False)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user_email', 'user_name', 'status', 'status_display',
            'shipping_address', 'shipping_address_id',
            'subtotal', 'shipping', 'total', 'items_count',
            'items', 'payment', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'subtotal', 'shipping', 'total', 'items_count',
            'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar pedido"""
    items = OrderItemCreateSerializer(many=True)
    shipping_address_id = serializers.UUIDField()
    
    class Meta:
        model = Order
        fields = ['shipping_address_id', 'items']
    
    def validate_items(self, value):
        """Valida que há pelo menos um item"""
        if not value:
            raise serializers.ValidationError("O pedido deve ter pelo menos um item.")
        return value
    
    def create(self, validated_data):
        """Cria pedido com seus itens"""
        from catalog.models import Product
        
        items_data = validated_data.pop('items')
        shipping_address_id = validated_data.pop('shipping_address_id')
        user = self.context['request'].user
        
        # Cria o pedido
        order = Order.objects.create(
            user=user,
            shipping_address_id=shipping_address_id,
            **validated_data
        )
        
        # Cria os itens do pedido
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            
            # Usa o preço atual do produto (ou desconto se houver)
            unit_price = product.discount_price if product.has_discount else product.price
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                unit_price=unit_price
            )
        
        # Calcula totais
        order.calculate_totals()
        
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar pedido (apenas status)"""
    
    class Meta:
        model = Order
        fields = ['status']
    
    def validate_status(self, value):
        """Valida transições de status"""
        order = self.instance
        
        # Regras de transição de status
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.PAID, OrderStatus.CANCELED],
            OrderStatus.PAID: [OrderStatus.PROCESSING, OrderStatus.CANCELED],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELED: [],
        }
        
        if order.status in valid_transitions:
            if value not in valid_transitions[order.status]:
                raise serializers.ValidationError(
                    f"Não é possível alterar o status de {order.get_status_display()} para {dict(OrderStatus.choices)[value]}."
                )
        
        return value


class CouponSerializer(serializers.ModelSerializer):
    """Serializer para Cupom"""
    is_valid = serializers.BooleanField(read_only=True)
    can_be_used = serializers.BooleanField(read_only=True)
    discount_display = serializers.CharField(source='get_discount_display', read_only=True)
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_value', 'discount_percentage',
            'max_uses', 'current_uses', 'valid_until', 'active',
            'is_valid', 'can_be_used', 'discount_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_uses', 'created_at', 'updated_at']


class CouponCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar cupom"""
    
    class Meta:
        model = Coupon
        fields = [
            'code', 'discount_value', 'discount_percentage',
            'max_uses', 'valid_until', 'active'
        ]
    
    def validate(self, data):
        """Valida que apenas um tipo de desconto seja fornecido"""
        discount_value = data.get('discount_value', 0)
        discount_percentage = data.get('discount_percentage', 0)
        
        if discount_value > 0 and discount_percentage > 0:
            raise serializers.ValidationError(
                "Forneça apenas um tipo de desconto: valor fixo OU porcentagem."
            )
        
        if discount_value == 0 and discount_percentage == 0:
            raise serializers.ValidationError(
                "Forneça pelo menos um tipo de desconto: valor fixo OU porcentagem."
            )
        
        return data
    
    def validate_code(self, value):
        """Valida formato do código"""
        if len(value) < 3:
            raise serializers.ValidationError("O código deve ter pelo menos 3 caracteres.")
        return value.upper()  # Converte para maiúsculas


class CouponValidateSerializer(serializers.Serializer):
    """Serializer para validar cupom"""
    code = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    def validate_code(self, value):
        """Valida se o cupom existe e é válido"""
        try:
            coupon = Coupon.objects.get(code=value.upper())
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Cupom não encontrado.")
        
        if not coupon.is_valid():
            raise serializers.ValidationError("Cupom inválido ou expirado.")
        
        if not coupon.can_be_used():
            raise serializers.ValidationError("Cupom atingiu o limite de usos.")
        
        return value.upper()
    
    def validate(self, data):
        """Calcula desconto se amount for fornecido"""
        code = data.get('code')
        amount = data.get('amount')
        
        if amount:
            try:
                coupon = Coupon.objects.get(code=code)
                discounted_amount = coupon.apply_discount(amount)
                data['discount'] = amount - discounted_amount
                data['final_amount'] = discounted_amount
            except Coupon.DoesNotExist:
                pass
        
        return data


class CouponUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar cupom"""
    
    class Meta:
        model = Coupon
        fields = [
            'code', 'discount_value', 'discount_percentage',
            'max_uses', 'valid_until', 'active'
        ]
    
    def validate(self, data):
        """Valida que apenas um tipo de desconto seja fornecido"""
        discount_value = data.get('discount_value', self.instance.discount_value if self.instance else 0)
        discount_percentage = data.get('discount_percentage', self.instance.discount_percentage if self.instance else 0)
        
        if discount_value > 0 and discount_percentage > 0:
            raise serializers.ValidationError(
                "Forneça apenas um tipo de desconto: valor fixo OU porcentagem."
            )
        
        if discount_value == 0 and discount_percentage == 0:
            raise serializers.ValidationError(
                "Forneça pelo menos um tipo de desconto: valor fixo OU porcentagem."
            )
        
        return data
    
    def validate_code(self, value):
        """Valida formato do código"""
        if len(value) < 3:
            raise serializers.ValidationError("O código deve ter pelo menos 3 caracteres.")
        return value.upper()
