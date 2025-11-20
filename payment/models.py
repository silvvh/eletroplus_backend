import uuid
from django.db import models
from django.conf import settings


class PaymentMethod(models.TextChoices):
    """Métodos de pagamento"""
    PIX = 'PIX', 'PIX'
    CREDIT_CARD = 'CREDIT_CARD', 'Cartão de Crédito'
    DEBIT_CARD = 'DEBIT_CARD', 'Cartão de Débito'
    BOLETO = 'BOLETO', 'Boleto'


class PaymentStatus(models.TextChoices):
    """Status do pagamento"""
    PENDING = 'PENDING', 'Pendente'
    PAID = 'PAID', 'Pago'
    FAILED = 'FAILED', 'Falhou'
    REFUNDED = 'REFUNDED', 'Reembolsado'


class Payment(models.Model):
    """Pagamento"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='pedido'
    )
    method = models.CharField(
        'método de pagamento',
        max_length=20,
        choices=PaymentMethod.choices
    )
    status = models.CharField(
        'status',
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    transaction_id = models.CharField(
        'ID da transação',
        max_length=255,
        blank=True,
        null=True,
        unique=True
    )
    amount = models.DecimalField(
        'valor',
        max_digits=10,
        decimal_places=2
    )
    paid_at = models.DateTimeField('pago em', null=True, blank=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'pagamento'
        verbose_name_plural = 'pagamentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"Pagamento #{self.id} - {self.get_method_display()} - {self.get_status_display()}"
    
    def mark_as_paid(self):
        """Marca pagamento como pago"""
        from django.utils import timezone
        
        if self.status == PaymentStatus.PENDING:
            self.status = PaymentStatus.PAID
            self.paid_at = timezone.now()
            self.save()
            
            # Atualiza status do pedido
            if self.order:
                self.order.status = 'PAID'
                self.order.save()
            
            return True
        return False
    
    def mark_as_failed(self):
        """Marca pagamento como falhou"""
        if self.status == PaymentStatus.PENDING:
            self.status = PaymentStatus.FAILED
            self.save()
            return True
        return False
    
    def mark_as_refunded(self):
        """Marca pagamento como reembolsado"""
        if self.status == PaymentStatus.PAID:
            self.status = PaymentStatus.REFUNDED
            self.save()
            
            # Atualiza status do pedido
            if self.order:
                self.order.status = 'CANCELED'
                self.order.save()
            
            return True
        return False
    
    @property
    def is_paid(self):
        """Verifica se o pagamento foi realizado"""
        return self.status == PaymentStatus.PAID
    
    @property
    def is_pending(self):
        """Verifica se o pagamento está pendente"""
        return self.status == PaymentStatus.PENDING
