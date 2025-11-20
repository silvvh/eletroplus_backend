import uuid

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from catalog.models import Product


class OrderStatus(models.TextChoices):
    """Status do pedido"""
    PENDING = 'PENDING', 'Pendente'
    PAID = 'PAID', 'Pago'
    PROCESSING = 'PROCESSING', 'Processando'
    SHIPPED = 'SHIPPED', 'Enviado'
    DELIVERED = 'DELIVERED', 'Entregue'
    CANCELED = 'CANCELED', 'Cancelado'


class Order(models.Model):
    """Pedido"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='usuário'
    )
    
    # Endereço de entrega (referencia ShippingAddress do usuário)
    shipping_address = models.ForeignKey(
        'users.ShippingAddress',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='endereço de entrega'
    )
    
    # Valores
    subtotal = models.DecimalField(
        'subtotal',
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    shipping = models.DecimalField(
        'frete',
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    total = models.DecimalField(
        'total',
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    
    # Status
    status = models.CharField(
        'status',
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    
    # Payment (será criado depois, por enquanto nullable)
    payment = models.ForeignKey(
        'payment.Payment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='pagamento'
    )
    
    # Cupom de desconto
    coupon = models.ForeignKey(
        'orders.Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='cupom'
    )
    
    # Timestamps
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.user.email} - {self.get_status_display()}"
    
    def calculate_totals(self):
        """Calcula subtotal, shipping e total do pedido"""
        # Calcula subtotal baseado nos itens
        self.subtotal = sum(item.total_price for item in self.items.all())
        
        # Aplica desconto do cupom se houver
        if self.coupon and self.coupon.is_valid():
            self.total = self.coupon.apply_discount(self.subtotal)
        else:
            self.total = self.subtotal
        
        # Calcula frete (pode ser implementada lógica mais complexa depois)
        # Por enquanto, frete fixo ou baseado em regras
        if self.subtotal > 500:  # Exemplo: frete grátis acima de R$ 500
            self.shipping = 0
        else:
            self.shipping = 15.00  # Frete padrão
        
        self.save()
    
    @property
    def items_count(self):
        """Retorna a quantidade total de itens no pedido"""
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    """Item do pedido"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='pedido'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='produto'
    )
    quantity = models.IntegerField(
        'quantidade',
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        'preço unitário',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_price = models.DecimalField(
        'preço total',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'item do pedido'
        verbose_name_plural = 'itens do pedido'
        ordering = ['created_at']
        unique_together = [['order', 'product']]  # Evita duplicatas do mesmo produto
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} - Pedido #{self.order.id}"
    
    def save(self, *args, **kwargs):
        """Calcula o preço total automaticamente"""
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        
        # Recalcula totais do pedido
        if self.order:
            self.order.calculate_totals()
    
    def delete(self, *args, **kwargs):
        """Recalcula totais do pedido ao deletar item"""
        order = self.order
        super().delete(*args, **kwargs)
        if order:
            order.calculate_totals()


class Coupon(models.Model):
    """Cupom de desconto"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField('código', max_length=50, unique=True)
    discount_value = models.DecimalField(
        'valor de desconto fixo',
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text='Desconto em valor fixo (ex: R$ 10,00)'
    )
    discount_percentage = models.IntegerField(
        'porcentagem de desconto',
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Desconto em porcentagem (ex: 10 para 10%)'
    )
    max_uses = models.IntegerField(
        'máximo de usos',
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Número máximo de vezes que o cupom pode ser usado'
    )
    current_uses = models.IntegerField(
        'usos atuais',
        default=0,
        validators=[MinValueValidator(0)]
    )
    valid_until = models.DateTimeField('válido até')
    active = models.BooleanField('ativo', default=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'cupom'
        verbose_name_plural = 'cupons'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'active']),
            models.Index(fields=['valid_until', 'active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.get_discount_display()}"
    
    def get_discount_display(self):
        """Retorna descrição do desconto"""
        if self.discount_percentage > 0:
            return f"{self.discount_percentage}%"
        elif self.discount_value > 0:
            return f"R$ {self.discount_value:.2f}"
        return "Sem desconto"
    
    def is_valid(self):
        """Verifica se o cupom é válido"""
        from django.utils import timezone
        
        if not self.active:
            return False
        
        if timezone.now() > self.valid_until:
            return False
        
        if self.current_uses >= self.max_uses:
            return False
        
        return True
    
    def can_be_used(self):
        """Verifica se o cupom pode ser usado"""
        return self.is_valid() and self.current_uses < self.max_uses
    
    def apply_discount(self, amount):
        """Aplica desconto ao valor"""
        if self.discount_percentage > 0:
            discount = (amount * self.discount_percentage) / 100
        else:
            discount = self.discount_value
        
        # Garante que o desconto não seja maior que o valor
        discount = min(discount, amount)
        
        return max(0, amount - discount)
    
    def use(self):
        """Incrementa contador de usos"""
        if self.can_be_used():
            self.current_uses += 1
            self.save()
            return True
        return False
    
    def release(self):
        """Libera um uso do cupom (quando pedido é cancelado)"""
        if self.current_uses > 0:
            self.current_uses -= 1
            self.save()
            return True
        return False
