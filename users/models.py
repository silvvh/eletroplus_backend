from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for EletroPlus e-commerce."""
    
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField('email address', unique=True)
    name = models.CharField('full name', max_length=255)
    phone = models.CharField('phone number', max_length=20, blank=True)
    
    # Address fields
    street = models.CharField('street address', max_length=255, blank=True)
    city = models.CharField('city', max_length=100, blank=True)
    state = models.CharField('state', max_length=100, blank=True)
    zip_code = models.CharField('zip code', max_length=20, blank=True)
    country = models.CharField('country', max_length=100, default='Brasil')
    
    # Status fields
    is_active = models.BooleanField('active', default=True)
    is_staff = models.BooleanField('staff status', default=False)
    date_joined = models.DateTimeField('date joined', default=timezone.now)
    last_login = models.DateTimeField('last login', blank=True, null=True)
    
    # E-commerce specific fields
    birth_date = models.DateField('birth date', null=True, blank=True)
    cpf = models.CharField('CPF', max_length=14, blank=True, unique=True, null=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the full name of the user."""
        return self.name
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.name.split()[0] if self.name else self.email


class ShippingAddress(models.Model):
    """Endereço de entrega do usuário (entidade fraca)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shipping_addresses',
        verbose_name='usuário'
    )
    street = models.CharField('rua', max_length=255)
    city = models.CharField('cidade', max_length=100)
    state = models.CharField('estado', max_length=100)
    zip_code = models.CharField('CEP', max_length=20)
    country = models.CharField('país', max_length=100, default='Brasil')
    complement = models.CharField('complemento', max_length=255, blank=True)
    number = models.CharField('número', max_length=20, blank=True)
    is_default = models.BooleanField('endereço padrão', default=False)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'endereço de entrega'
        verbose_name_plural = 'endereços de entrega'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.street}, {self.number} - {self.city}/{self.state}"
    
    def save(self, *args, **kwargs):
        """Garante que apenas um endereço seja padrão por usuário"""
        if self.is_default:
            # Remove o padrão de outros endereços do mesmo usuário
            ShippingAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
