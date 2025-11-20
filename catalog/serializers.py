from rest_framework import serializers
from .models import Category, Product, ProductSpecification


class ProductSpecificationSerializer(serializers.ModelSerializer):
    """Serializer para Especificação Técnica"""
    
    class Meta:
        model = ProductSpecification
        fields = ['id', 'key', 'value', 'created_at']
        read_only_fields = ['id', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para Categoria"""
    products_count = serializers.IntegerField(source='products.count', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'products_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class CategoryDetailSerializer(CategorySerializer):
    """Serializer detalhado para Categoria com produtos"""
    products = serializers.SerializerMethodField()
    
    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['products']
    
    def get_products(self, obj):
        """Retorna lista resumida de produtos da categoria"""
        products = obj.products.all()[:10]  # Limita a 10 produtos
        return ProductListSerializer(products, many=True).data


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer resumido para lista de produtos"""
    category = CategorySerializer(read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'brand', 'model', 'category',
            'price', 'discount_price', 'has_discount', 'discount_percentage',
            'stock', 'rating', 'rating_count',
            'image_urls', 'is_featured', 'created_at'
        ]
        read_only_fields = ['id', 'rating', 'rating_count', 'created_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para produto com especificações"""
    category = CategorySerializer(read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'brand', 'model', 'category',
            'price', 'discount_price', 'has_discount', 'discount_percentage',
            'stock', 'rating', 'rating_count',
            'image_urls', 'is_featured',
            'specifications', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'rating', 'rating_count', 'created_at', 'updated_at']


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criar/atualizar produto"""
    specifications = ProductSpecificationSerializer(many=True, required=False)
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'brand', 'model', 'category',
            'price', 'discount_price', 'stock',
            'image_urls', 'is_featured', 'specifications'
        ]
    
    def create(self, validated_data):
        """Cria produto com suas especificações"""
        specifications_data = validated_data.pop('specifications', [])
        product = Product.objects.create(**validated_data)
        
        for spec_data in specifications_data:
            ProductSpecification.objects.create(product=product, **spec_data)
        
        return product
    
    def update(self, instance, validated_data):
        """Atualiza produto e suas especificações"""
        specifications_data = validated_data.pop('specifications', None)
        
        # Atualiza campos do produto
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Atualiza especificações se fornecidas
        if specifications_data is not None:
            # Remove especificações antigas
            instance.specifications.all().delete()
            # Cria novas especificações
            for spec_data in specifications_data:
                ProductSpecification.objects.create(product=instance, **spec_data)
        
        return instance
