from rest_framework import serializers
from .models import Banner


class BannerSerializer(serializers.ModelSerializer):
    """Serializer para Banner"""
    
    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'subtitle', 'image_url',
            'link', 'active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BannerCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar banner"""
    
    class Meta:
        model = Banner
        fields = ['title', 'subtitle', 'image_url', 'link', 'active', 'order']
    
    def validate_title(self, value):
        """Valida título"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("O título deve ter pelo menos 3 caracteres.")
        return value.strip()
    
    def validate_image_url(self, value):
        """Valida URL da imagem"""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("A URL da imagem deve começar com http:// ou https://")
        return value
    
    def validate_link(self, value):
        """Valida link"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("O link deve começar com http:// ou https://")
        return value


class BannerUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar banner"""
    
    class Meta:
        model = Banner
        fields = ['title', 'subtitle', 'image_url', 'link', 'active', 'order']
    
    def validate_title(self, value):
        """Valida título"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("O título deve ter pelo menos 3 caracteres.")
        return value.strip()
    
    def validate_image_url(self, value):
        """Valida URL da imagem"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("A URL da imagem deve começar com http:// ou https://")
        return value
    
    def validate_link(self, value):
        """Valida link"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("O link deve começar com http:// ou https://")
        return value
