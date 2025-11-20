from rest_framework import serializers
from .models import Payment, PaymentMethod, PaymentStatus
from orders.serializers import OrderListSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer para Pagamento"""
    order = OrderListSerializer(read_only=True)
    order_id = serializers.UUIDField(write_only=True)
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_id', 'method', 'method_display',
            'status', 'status_display', 'transaction_id', 'amount',
            'paid_at', 'is_paid', 'is_pending', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'paid_at', 'created_at', 'updated_at']
    
    def validate_method(self, value):
        """Valida método de pagamento"""
        if value not in [choice[0] for choice in PaymentMethod.choices]:
            raise serializers.ValidationError("Método de pagamento inválido.")
        return value
    
    def validate_status(self, value):
        """Valida status do pagamento"""
        if value not in [choice[0] for choice in PaymentStatus.choices]:
            raise serializers.ValidationError("Status de pagamento inválido.")
        return value


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar pagamento"""
    order_id = serializers.UUIDField()
    
    class Meta:
        model = Payment
        fields = ['order_id', 'method', 'transaction_id', 'amount']
    
    def validate_order_id(self, value):
        """Valida se o pedido existe e pertence ao usuário"""
        from orders.models import Order
        
        try:
            order = Order.objects.get(id=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Pedido não encontrado.")
        
        # Verifica se o pedido pertence ao usuário (se não for admin)
        request = self.context.get('request')
        if request and not request.user.is_staff:
            if order.user != request.user:
                raise serializers.ValidationError("Você não tem permissão para criar pagamento para este pedido.")
        
        return value
    
    def create(self, validated_data):
        """Cria pagamento associado ao pedido"""
        from orders.models import Order
        
        order_id = validated_data.pop('order_id')
        order = Order.objects.get(id=order_id)
        
        # Define o valor como o total do pedido
        amount = validated_data.get('amount', order.total)
        
        payment = Payment.objects.create(
            order=order,
            amount=amount,
            **validated_data
        )
        
        return payment


class PaymentUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar pagamento (apenas status e transaction_id)"""
    
    class Meta:
        model = Payment
        fields = ['status', 'transaction_id']
    
    def validate_status(self, value):
        """Valida transições de status"""
        payment = self.instance
        
        # Regras de transição de status
        valid_transitions = {
            PaymentStatus.PENDING: [PaymentStatus.PAID, PaymentStatus.FAILED],
            PaymentStatus.PAID: [PaymentStatus.REFUNDED],
            PaymentStatus.FAILED: [PaymentStatus.PENDING],  # Pode tentar novamente
            PaymentStatus.REFUNDED: [],
        }
        
        if payment.status in valid_transitions:
            if value not in valid_transitions[payment.status]:
                raise serializers.ValidationError(
                    f"Não é possível alterar o status de {payment.get_status_display()} para {dict(PaymentStatus.choices)[value]}."
                )
        
        return value
    
    def update(self, instance, validated_data):
        """Atualiza pagamento e marca como pago se necessário"""
        status = validated_data.get('status')
        
        if status == PaymentStatus.PAID:
            instance.mark_as_paid()
        elif status == PaymentStatus.FAILED:
            instance.mark_as_failed()
        elif status == PaymentStatus.REFUNDED:
            instance.mark_as_refunded()
        else:
            instance.status = status
            instance.save()
        
        # Atualiza transaction_id se fornecido
        if 'transaction_id' in validated_data:
            instance.transaction_id = validated_data['transaction_id']
            instance.save()
        
        return instance
