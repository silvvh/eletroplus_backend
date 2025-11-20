import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from catalog.models import Product


class Cart(models.Model):
    """Carrinho de compras"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='usuário'
    )
    
    # Valores
    subtotal = models.DecimalField(
        'subtotal',
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
    
    # Cupom de desconto
    coupon = models.ForeignKey(
        'orders.Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts',
        verbose_name='cupom'
    )
    
    # Timestamps
    updated_at = models.DateTimeField('atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'carrinho'
        verbose_name_plural = 'carrinhos'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Carrinho de {self.user.email}"
    
    def calculate_totals(self):
        """Calcula subtotal e total do carrinho"""
        # Calcula subtotal baseado nos itens
        self.subtotal = sum(item.total_price for item in self.items.all())
        
        # Aplica desconto do cupom se houver
        if self.coupon and self.coupon.is_valid():
            self.total = self.coupon.apply_discount(self.subtotal)
        else:
            self.total = self.subtotal
        
        self.save()
    
    @property
    def items_count(self):
        """Retorna a quantidade total de itens no carrinho"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def is_empty(self):
        """Verifica se o carrinho está vazio"""
        return self.items.count() == 0


class CartItem(models.Model):
    """Item do carrinho"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='carrinho'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='produto'
    )
    quantity = models.IntegerField(
        'quantidade',
        default=1,
        validators=[MinValueValidator(1)]
    )
    price_at_time = models.DecimalField(
        'preço no momento',
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
    updated_at = models.DateTimeField('atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'item do carrinho'
        verbose_name_plural = 'itens do carrinho'
        ordering = ['updated_at']
        unique_together = [['cart', 'product']]  # Evita duplicatas do mesmo produto
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} - {self.cart.user.email}"
    
    def save(self, *args, **kwargs):
        """Calcula o preço total e reserva estoque"""
        is_new = self._state.adding
        
        # Se é um novo item ou quantidade mudou, gerencia reserva
        if is_new:
            # Novo item - cria reserva
            old_quantity = 0
        else:
            # Item existente - verifica mudança de quantidade
            try:
                old_item = CartItem.objects.get(pk=self.pk)
                old_quantity = old_item.quantity
            except CartItem.DoesNotExist:
                old_quantity = 0
        
        # Calcula o preço total
        self.total_price = self.price_at_time * self.quantity
        
        # Gerencia reserva de estoque
        if is_new or self.quantity != old_quantity:
            # Libera reserva antiga se quantidade mudou
            if not is_new and old_quantity > 0:
                self.product.release_stock_reservation(cart_item=self)
            
            # Cria nova reserva
            try:
                self.product.reserve_stock(
                    quantity=self.quantity,
                    cart_item=self,
                    expiration_minutes=30  # Reserva expira em 30 minutos
                )
            except ValueError as e:
                # Se não houver estoque, não salva o item
                raise ValueError(str(e))
        
        super().save(*args, **kwargs)
        
        # Recalcula totais do carrinho
        if self.cart:
            self.cart.calculate_totals()
    
    def delete(self, *args, **kwargs):
        """Libera reserva de estoque ao deletar item"""
        # Libera reserva antes de deletar
        if self.product:
            self.product.release_stock_reservation(cart_item=self)
        
        cart = self.cart
        super().delete(*args, **kwargs)
        if cart:
            cart.calculate_totals()
