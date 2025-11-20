from rest_framework import serializers
from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer para Mensagem de Contato"""
    
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'name', 'email', 'phone', 'subject',
            'message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ContactMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar mensagem de contato"""
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
    
    def validate_email(self, value):
        """Valida formato do email"""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Email inválido.")
        
        return value.lower()
    
    def validate_subject(self, value):
        """Valida assunto"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("O assunto deve ter pelo menos 3 caracteres.")
        return value.strip()
    
    def validate_message(self, value):
        """Valida mensagem"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("A mensagem deve ter pelo menos 10 caracteres.")
        return value.strip()


class ContactMessageDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para mensagem (apenas para admin)"""
    
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'name', 'email', 'phone', 'subject',
            'message', 'is_read', 'replied_at', 'notes',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'replied_at']
