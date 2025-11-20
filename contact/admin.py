from django.contrib import admin
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Admin para Mensagem de Contato"""
    list_display = ('name', 'email', 'subject', 'is_read', 'created_at', 'replied_at')
    list_filter = ('is_read', 'created_at', 'replied_at')
    search_fields = ('name', 'email', 'subject', 'message', 'phone')
    readonly_fields = ('id', 'created_at', 'replied_at')
    
    fieldsets = (
        ('Informações do Contato', {
            'fields': ('id', 'name', 'email', 'phone')
        }),
        ('Mensagem', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'replied_at')
        }),
        ('Observações Internas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Marca mensagens como lidas"""
        count = queryset.update(is_read=True)
        self.message_user(request, f'{count} mensagem(ns) marcada(s) como lida(s).')
    mark_as_read.short_description = 'Marcar como lida'
    
    def mark_as_replied(self, request, queryset):
        """Marca mensagens como respondidas"""
        from django.utils import timezone
        count = queryset.update(is_read=True, replied_at=timezone.now())
        self.message_user(request, f'{count} mensagem(ns) marcada(s) como respondida(s).')
    mark_as_replied.short_description = 'Marcar como respondida'
    
    def mark_as_unread(self, request, queryset):
        """Marca mensagens como não lidas"""
        count = queryset.update(is_read=False, replied_at=None)
        self.message_user(request, f'{count} mensagem(ns) marcada(s) como não lida(s).')
    mark_as_unread.short_description = 'Marcar como não lida'
