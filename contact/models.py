import uuid
from django.db import models
from django.core.validators import EmailValidator


class ContactMessage(models.Model):
    """Mensagem de contato / SAC"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('nome', max_length=255)
    email = models.EmailField('email', validators=[EmailValidator()])
    phone = models.CharField('telefone', max_length=20, blank=True)
    subject = models.CharField('assunto', max_length=255)
    message = models.TextField('mensagem')
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    
    # Campos opcionais para controle interno
    is_read = models.BooleanField('lido', default=False)
    replied_at = models.DateTimeField('respondido em', null=True, blank=True)
    notes = models.TextField('observações', blank=True, help_text='Notas internas sobre o atendimento')
    
    class Meta:
        verbose_name = 'mensagem de contato'
        verbose_name_plural = 'mensagens de contato'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.subject} - {self.created_at.strftime('%d/%m/%Y')}"
    
    def mark_as_read(self):
        """Marca mensagem como lida"""
        self.is_read = True
        self.save()
    
    def mark_as_replied(self):
        """Marca mensagem como respondida"""
        from django.utils import timezone
        self.is_read = True
        self.replied_at = timezone.now()
        self.save()
