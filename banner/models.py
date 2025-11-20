import uuid
from django.db import models


class Banner(models.Model):
    """Banner / Promoção da Home"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('título', max_length=255)
    subtitle = models.CharField('subtítulo', max_length=255, blank=True)
    image_url = models.URLField('URL da imagem', max_length=500)
    link = models.URLField('link', max_length=500, blank=True, help_text='Link para onde o banner redireciona')
    active = models.BooleanField('ativo', default=True)
    
    # Campos opcionais para controle
    order = models.IntegerField(
        'ordem de exibição',
        default=0,
        help_text='Banners com ordem menor aparecem primeiro'
    )
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'banner'
        verbose_name_plural = 'banners'
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['active', 'order']),
        ]
    
    def __str__(self):
        return f"{self.title} - {'Ativo' if self.active else 'Inativo'}"
