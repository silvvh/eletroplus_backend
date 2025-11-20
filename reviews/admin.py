from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin para Avaliação"""
    list_display = ('id', 'user', 'product', 'rating', 'created_at', 'updated_at')
    list_filter = ('rating', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__name', 'product__name', 'product__brand', 'comment')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'user', 'product', 'rating')
        }),
        ('Conteúdo', {
            'fields': ('comment', 'images')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Torna campos readonly"""
        return self.readonly_fields
