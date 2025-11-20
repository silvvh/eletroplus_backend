from django.contrib import admin
from .models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """Admin para Banner"""
    list_display = ('title', 'subtitle', 'active', 'order', 'created_at', 'updated_at')
    list_filter = ('active', 'created_at', 'updated_at')
    search_fields = ('title', 'subtitle')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'title', 'subtitle')
        }),
        ('Mídia e Link', {
            'fields': ('image_url', 'link')
        }),
        ('Configurações', {
            'fields': ('active', 'order')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['activate', 'deactivate']
    
    def activate(self, request, queryset):
        """Ativa banners"""
        count = queryset.update(active=True)
        self.message_user(request, f'{count} banner(s) ativado(s).')
    activate.short_description = 'Ativar banners selecionados'
    
    def deactivate(self, request, queryset):
        """Desativa banners"""
        count = queryset.update(active=False)
        self.message_user(request, f'{count} banner(s) desativado(s).')
    deactivate.short_description = 'Desativar banners selecionados'
