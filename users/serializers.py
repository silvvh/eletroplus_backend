from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, ShippingAddress


class UserSerializer(serializers.ModelSerializer):
    """Serializer para Usuário"""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'phone',
            'street', 'city', 'state', 'zip_code', 'country',
            'birth_date', 'cpf', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de usuário"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Senha do usuário (mínimo 8 caracteres)',
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Confirmação da senha (deve ser igual à senha)'
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'name', 'phone', 'password', 'password_confirm',
            'street', 'city', 'state', 'zip_code', 'country',
            'birth_date', 'cpf'
        ]
        extra_kwargs = {
            'email': {
                'required': True,
                'help_text': 'Email do usuário (deve ser único)'
            },
            'name': {
                'required': True,
                'help_text': 'Nome completo do usuário'
            },
            'phone': {
                'required': False,
                'allow_blank': True,
                'help_text': 'Telefone do usuário'
            },
            'street': {
                'required': False,
                'allow_blank': True,
                'help_text': 'Rua/Endereço'
            },
            'city': {
                'required': False,
                'allow_blank': True,
                'help_text': 'Cidade'
            },
            'state': {
                'required': False,
                'allow_blank': True,
                'help_text': 'Estado'
            },
            'zip_code': {
                'required': False,
                'allow_blank': True,
                'help_text': 'CEP'
            },
            'country': {
                'required': False,
                'default': 'Brasil',
                'help_text': 'País'
            },
            'birth_date': {
                'required': False,
                'allow_null': True,
                'help_text': 'Data de nascimento (formato: YYYY-MM-DD)'
            },
            'cpf': {
                'required': False,
                'allow_blank': True,
                'allow_null': True,
                'help_text': 'CPF do usuário (deve ser único)'
            },
        }
    
    def validate(self, attrs):
        """Valida se as senhas coincidem"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs
    
    def create(self, validated_data):
        """Cria novo usuário"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)  # Hash da senha
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer customizado para tokens JWT"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Adiciona informações customizadas ao token
        token['email'] = user.email
        token['name'] = user.name
        
        return token


class ShippingAddressSerializer(serializers.ModelSerializer):
    """Serializer para Endereço de Entrega"""
    
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'street', 'city', 'state', 'zip_code', 'country',
            'complement', 'number', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
