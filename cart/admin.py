from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Inline para itens do carrinho"""
    model = CartItem
    extra = 0
    fields = ('product', 'quantity', 'price_at_time', 'total_price')
    readonly_fields = ('total_price',)
    can_delete = True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin para Carrinho"""
    list_display = ('id', 'user', 'subtotal', 'total', 'items_count', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('id', 'user__email', 'user__name', 'coupon_code')
    readonly_fields = ('id', 'subtotal', 'total', 'items_count', 'updated_at')
    inlines = [CartItemInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'user')
        }),
        ('Valores', {
            'fields': ('subtotal', 'total', 'items_count')
        }),
        ('Cupom', {
            'fields': ('coupon_code',)
        }),
        ('Datas', {
            'fields': ('updated_at',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Torna valores readonly (calculados automaticamente)"""
        return self.readonly_fields
    
    def items_count(self, obj):
        """Retorna quantidade de itens"""
        return obj.items_count
    items_count.short_description = 'Qtd. Itens'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin para Item do Carrinho"""
    list_display = ('id', 'cart', 'product', 'quantity', 'price_at_time', 'total_price', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('cart__user__email', 'product__name', 'product__brand')
    readonly_fields = ('id', 'total_price', 'updated_at')
    
    fieldsets = (
        ('Informações', {
            'fields': ('id', 'cart', 'product', 'quantity', 'price_at_time', 'total_price')
        }),
        ('Datas', {
            'fields': ('updated_at',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Torna total_price readonly (calculado automaticamente)"""
        return self.readonly_fields
