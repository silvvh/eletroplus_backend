import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from catalog.models import Product


class Review(models.Model):
    """Avaliação de produto"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='usuário'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='produto'
    )
    rating = models.IntegerField(
        'avaliação',
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField('comentário')
    images = models.JSONField('imagens', default=list, blank=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'avaliação'
        verbose_name_plural = 'avaliações'
        ordering = ['-created_at']
        unique_together = [['user', 'product']]  # Um usuário pode avaliar um produto apenas uma vez
        indexes = [
            models.Index(fields=['product', 'rating']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name} - {self.rating}⭐"
    
    def save(self, *args, **kwargs):
        """Salva review e atualiza média do produto"""
        is_new = self._state.adding
        
        if is_new:
            # Nova review - atualiza média
            old_rating = None
        else:
            # Review existente - pega rating antigo
            try:
                old_review = Review.objects.get(pk=self.pk)
                old_rating = old_review.rating
            except Review.DoesNotExist:
                old_rating = None
        
        super().save(*args, **kwargs)
        
        # Atualiza média de avaliações do produto
        self.product.update_rating()
    
    def delete(self, *args, **kwargs):
        """Deleta review e atualiza média do produto"""
        product = self.product
        super().delete(*args, **kwargs)
        
        # Atualiza média de avaliações do produto
        if product:
            product.update_rating()
