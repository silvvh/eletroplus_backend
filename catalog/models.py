import uuid
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class Category(models.Model):
    """Categoria de produtos (ex: Geladeira, Fogão, Micro-ondas)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('nome', max_length=100, unique=True)
    slug = models.SlugField('slug', max_length=100, unique=True, blank=True)
    icon = models.CharField('ícone', max_length=50, blank=True, null=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Gera o slug automaticamente se não fornecido"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Produto de eletrodoméstico"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('nome', max_length=255)
    description = models.TextField('descrição')
    brand = models.CharField('marca', max_length=100)
    model = models.CharField('modelo', max_length=100)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='categoria'
    )
    
    # Preços
    price = models.DecimalField(
        'preço',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discount_price = models.DecimalField(
        'preço com desconto',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Estoque e avaliações
    stock = models.IntegerField('estoque', default=0, validators=[MinValueValidator(0)])
    rating = models.FloatField(
        'avaliação média',
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    rating_count = models.IntegerField('quantidade de avaliações', default=0)
    
    # Imagens (armazenadas como JSON)
    image_urls = models.JSONField('URLs das imagens', default=list, blank=True)
    
    is_featured = models.BooleanField('destaque', default=False)
    
    # Timestamps
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'produto'
        verbose_name_plural = 'produtos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_featured']),
            models.Index(fields=['brand']),
            models.Index(fields=['-rating']),
        ]
    
    def __str__(self):
        return f"{self.brand} {self.name}"
    
    @property
    def has_discount(self):
        """Verifica se o produto tem desconto"""
        return self.discount_price is not None and self.discount_price < self.price
    
    @property
    def discount_percentage(self):
        """Calcula a porcentagem de desconto"""
        if self.has_discount:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def available_stock(self):
        """Retorna estoque disponível (estoque total - reservas ativas)"""
        from django.utils import timezone
        from .models import StockReservation
        
        # Soma todas as reservas ativas
        active_reservations = StockReservation.objects.filter(
            product=self,
            status='RESERVED',
            expires_at__gt=timezone.now()
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
        return max(0, self.stock - active_reservations)

    def reserve_stock(self, quantity, cart_item=None, order=None, expiration_minutes=30):
        """Reserva estoque para um item do carrinho ou pedido"""
        from django.utils import timezone
        from datetime import timedelta
        from .models import StockReservation
        
        # Verifica estoque disponível
        if quantity > self.available_stock:
            raise ValueError(f'Estoque insuficiente. Disponível: {self.available_stock}')
        
        # Cria reserva
        expires_at = timezone.now() + timedelta(minutes=expiration_minutes)
        reservation = StockReservation.objects.create(
            product=self,
            cart_item=cart_item,
            order=order,
            quantity=quantity,
            expires_at=expires_at
        )
        
        return reservation

    def release_stock_reservation(self, cart_item=None, order=None):
        """Libera reserva de estoque"""
        from .models import StockReservation
        
        if cart_item:
            reservations = StockReservation.objects.filter(
                product=self,
                cart_item=cart_item,
                status='RESERVED'
            )
        elif order:
            reservations = StockReservation.objects.filter(
                product=self,
                order=order,
                status='RESERVED'
            )
        else:
            return False
        
        for reservation in reservations:
            reservation.release()
        
        return True

    def convert_reservation_to_sale(self, order, quantity):
        """Converte reserva em venda (reduz estoque)"""
        from .models import StockReservation
        
        # Marca reservas como convertidas
        reservations = StockReservation.objects.filter(
            product=self,
            cart_item__cart__user=order.user,
            status='RESERVED'
        )[:quantity]
        
        for reservation in reservations:
            reservation.status = 'CONVERTED'
            reservation.order = order
            reservation.save()
        
        # Reduz estoque
        self.stock -= quantity
        self.save()
        
        return True

    def update_rating(self):
        """Atualiza a média de avaliações do produto"""
        from reviews.models import Review
        
        reviews = Review.objects.filter(product=self)
        
        if reviews.exists():
            # Calcula média
            total_rating = sum(review.rating for review in reviews)
            self.rating = round(total_rating / reviews.count(), 2)
            self.rating_count = reviews.count()
        else:
            # Sem avaliações
            self.rating = 0.0
            self.rating_count = 0
        
        self.save(update_fields=['rating', 'rating_count'])


class ProductSpecification(models.Model):
    """Especificação técnica do produto"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='specifications',
        verbose_name='produto'
    )
    key = models.CharField('chave', max_length=100)  # ex: "Capacidade", "Voltagem"
    value = models.CharField('valor', max_length=255)  # ex: "300L", "220V"
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'especificação técnica'
        verbose_name_plural = 'especificações técnicas'
        ordering = ['key']
        unique_together = [['product', 'key']]  # Evita duplicatas da mesma especificação
    
    def __str__(self):
        return f"{self.key}: {self.value} ({self.product.name})"


class StockReservation(models.Model):
    """Reserva de estoque para itens no carrinho"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_reservations',
        verbose_name='produto'
    )
    cart_item = models.ForeignKey(
        'cart.CartItem',
        on_delete=models.CASCADE,
        related_name='stock_reservation',
        verbose_name='item do carrinho',
        null=True,
        blank=True
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='stock_reservations',
        verbose_name='pedido',
        null=True,
        blank=True
    )
    quantity = models.IntegerField('quantidade reservada', validators=[MinValueValidator(1)])
    status = models.CharField(
        'status',
        max_length=20,
        choices=[
            ('RESERVED', 'Reservado'),
            ('CONVERTED', 'Convertido em venda'),
            ('EXPIRED', 'Expirado'),
            ('RELEASED', 'Liberado'),
        ],
        default='RESERVED'
    )
    expires_at = models.DateTimeField('expira em')
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'reserva de estoque'
        verbose_name_plural = 'reservas de estoque'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['expires_at', 'status']),
        ]
    
    def __str__(self):
        return f"Reserva de {self.quantity}x {self.product.name} - {self.get_status_display()}"
    
    def is_expired(self):
        """Verifica se a reserva expirou"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def release(self):
        """Libera a reserva de estoque"""
        if self.status == 'RESERVED':
            self.status = 'RELEASED'
            self.save()
            return True
        return False
