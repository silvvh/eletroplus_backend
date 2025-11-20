from django.contrib import admin
from .models import Category, Product, ProductSpecification, StockReservation


class ProductSpecificationInline(admin.TabularInline):
    """Inline para especificações técnicas do produto"""
    model = ProductSpecification
    extra = 1
    fields = ('key', 'value')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin para Categoria"""
    list_display = ('name', 'slug', 'icon', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'slug', 'icon')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin para Produto"""
    list_display = ('name', 'brand', 'category', 'price', 'stock', 'rating', 'is_featured', 'created_at')
    list_filter = ('category', 'brand', 'is_featured', 'created_at')
    search_fields = ('name', 'brand', 'model', 'description')
    readonly_fields = ('id', 'rating', 'rating_count', 'created_at', 'updated_at', 'has_discount', 'discount_percentage')
    inlines = [ProductSpecificationInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'description', 'brand', 'model', 'category')
        }),
        ('Preços', {
            'fields': ('price', 'discount_price', 'has_discount', 'discount_percentage')
        }),
        ('Estoque e Avaliações', {
            'fields': ('stock', 'rating', 'rating_count')
        }),
        ('Mídia', {
            'fields': ('image_urls',)
        }),
        ('Configurações', {
            'fields': ('is_featured',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Torna rating e rating_count readonly (calculados automaticamente)"""
        return self.readonly_fields


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    """Admin para Especificação Técnica"""
    list_display = ('product', 'key', 'value', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'key', 'value')
    readonly_fields = ('id', 'created_at')
    
    fieldsets = (
        ('Informações', {
            'fields': ('id', 'product', 'key', 'value')
        }),
        ('Datas', {
            'fields': ('created_at',)
        }),
    )


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    """Admin para Reserva de Estoque"""
    list_display = ('id', 'product', 'quantity', 'status', 'expires_at', 'created_at')
    list_filter = ('status', 'created_at', 'expires_at')
    search_fields = ('product__name', 'product__brand')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informações', {
            'fields': ('id', 'product', 'cart_item', 'order', 'quantity', 'status')
        }),
        ('Datas', {
            'fields': ('expires_at', 'created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        """Filtra reservas expiradas"""
        from django.utils import timezone
        # Atualiza status de reservas expiradas
        StockReservation.objects.filter(
            status='RESERVED',
            expires_at__lt=timezone.now()
        ).update(status='EXPIRED')
        
        return super().get_queryset(request)
