from django.contrib import admin
from .models import Order, OrderItem, OrderStatus, Coupon


class OrderItemInline(admin.TabularInline):
    """Inline para itens do pedido"""
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('total_price',)
    can_delete = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin para Pedido"""
    list_display = ('id', 'user', 'status', 'total', 'items_count', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('id', 'user__email', 'user__name')
    readonly_fields = ('id', 'subtotal', 'shipping', 'total', 'items_count', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'user', 'status')
        }),
        ('Endereço de Entrega', {
            'fields': ('shipping_address',)
        }),
        ('Valores', {
            'fields': ('subtotal', 'shipping', 'total', 'items_count')
        }),
        ('Pagamento', {
            'fields': ('payment',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Torna valores readonly (calculados automaticamente)"""
        return self.readonly_fields
    
    def items_count(self, obj):
        """Retorna quantidade de itens"""
        return obj.items_count
    items_count.short_description = 'Qtd. Itens'
    
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_canceled']
    
    def mark_as_processing(self, request, queryset):
        """Marca pedidos como processando"""
        queryset.update(status=OrderStatus.PROCESSING)
    mark_as_processing.short_description = 'Marcar como Processando'
    
    def mark_as_shipped(self, request, queryset):
        """Marca pedidos como enviado"""
        queryset.update(status=OrderStatus.SHIPPED)
    mark_as_shipped.short_description = 'Marcar como Enviado'
    
    def mark_as_delivered(self, request, queryset):
        """Marca pedidos como entregue"""
        queryset.update(status=OrderStatus.DELIVERED)
    mark_as_delivered.short_description = 'Marcar como Entregue'
    
    def mark_as_canceled(self, request, queryset):
        """Marca pedidos como cancelado"""
        queryset.update(status=OrderStatus.CANCELED)
    mark_as_canceled.short_description = 'Marcar como Cancelado'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin para Item do Pedido"""
    list_display = ('id', 'order', 'product', 'quantity', 'unit_price', 'total_price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('order__id', 'product__name', 'product__brand')
    readonly_fields = ('id', 'total_price', 'created_at')
    
    fieldsets = (
        ('Informações', {
            'fields': ('id', 'order', 'product', 'quantity', 'unit_price', 'total_price')
        }),
        ('Datas', {
            'fields': ('created_at',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Torna total_price readonly (calculado automaticamente)"""
        return self.readonly_fields


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Admin para Cupom"""
    list_display = ('code', 'discount_value', 'discount_percentage', 'current_uses', 'max_uses', 'valid_until', 'active', 'created_at')
    list_filter = ('active', 'created_at', 'valid_until')
    search_fields = ('code',)
    readonly_fields = ('id', 'current_uses', 'created_at', 'updated_at', 'is_valid', 'can_be_used')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'code', 'active')
        }),
        ('Desconto', {
            'fields': ('discount_value', 'discount_percentage'),
            'description': 'Preencha apenas um dos campos: valor fixo OU porcentagem'
        }),
        ('Limites', {
            'fields': ('max_uses', 'current_uses', 'valid_until')
        }),
        ('Status', {
            'fields': ('is_valid', 'can_be_used')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def is_valid(self, obj):
        """Mostra se o cupom é válido"""
        if obj:
            return obj.is_valid()
        return False
    is_valid.boolean = True
    is_valid.short_description = 'Válido'
    
    def can_be_used(self, obj):
        """Mostra se o cupom pode ser usado"""
        if obj:
            return obj.can_be_used()
        return False
    can_be_used.boolean = True
    can_be_used.short_description = 'Pode Usar'
