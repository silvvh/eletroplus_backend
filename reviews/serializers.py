from rest_framework import serializers
from .models import Review
from users.serializers import UserSerializer
from catalog.serializers import ProductListSerializer


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer para Avaliação"""
    user = UserSerializer(read_only=True)
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'product', 'product_id', 'rating',
            'comment', 'images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'product', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Valida rating entre 1 e 5"""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("A avaliação deve ser entre 1 e 5.")
        return value
    
    def validate(self, data):
        """Valida que o usuário não avaliou o produto duas vezes"""
        request = self.context.get('request')
        product_id = data.get('product_id')
        
        if request and product_id:
            # Verifica se já existe review do usuário para este produto
            existing_review = Review.objects.filter(
                user=request.user,
                product_id=product_id
            ).first()
            
            # Se estiver atualizando, permite
            if self.instance and existing_review and existing_review.id == self.instance.id:
                return data
            
            # Se for nova review e já existe, não permite
            if not self.instance and existing_review:
                raise serializers.ValidationError(
                    "Você já avaliou este produto. Você pode editar sua avaliação existente."
                )
        
        return data


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar avaliação"""
    product_id = serializers.UUIDField()
    
    class Meta:
        model = Review
        fields = ['product_id', 'rating', 'comment', 'images']
    
    def validate_rating(self, value):
        """Valida rating entre 1 e 5"""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("A avaliação deve ser entre 1 e 5.")
        return value
    
    def validate(self, data):
        """Valida que o usuário comprou o produto antes de avaliar"""
        request = self.context.get('request')
        product_id = data.get('product_id')
        
        if request and product_id:
            # Verifica se o usuário já comprou o produto
            from orders.models import OrderItem
            
            has_purchased = OrderItem.objects.filter(
                order__user=request.user,
                product_id=product_id,
                order__status__in=['PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED']
            ).exists()
            
            if not has_purchased and not request.user.is_staff:
                raise serializers.ValidationError(
                    "Você precisa ter comprado este produto para avaliá-lo."
                )
            
            # Verifica se já existe review
            existing_review = Review.objects.filter(
                user=request.user,
                product_id=product_id
            ).exists()
            
            if existing_review:
                raise serializers.ValidationError(
                    "Você já avaliou este produto. Você pode editar sua avaliação existente."
                )
        
        return data
    
    def create(self, validated_data):
        """Cria avaliação associada ao usuário"""
        product_id = validated_data.pop('product_id')
        user = self.context['request'].user
        
        review = Review.objects.create(
            user=user,
            product_id=product_id,
            **validated_data
        )
        
        return review


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar avaliação"""
    
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'images']
    
    def validate_rating(self, value):
        """Valida rating entre 1 e 5"""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("A avaliação deve ser entre 1 e 5.")
        return value
