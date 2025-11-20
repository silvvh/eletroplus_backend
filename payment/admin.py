from django.contrib import admin
from .models import Payment, PaymentMethod, PaymentStatus


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin para Pagamento"""
    list_display = ('id', 'order', 'method', 'status', 'amount', 'paid_at', 'created_at')
    list_filter = ('method', 'status', 'created_at', 'paid_at')
    search_fields = ('id', 'order__id', 'transaction_id', 'order__user__email')
    readonly_fields = ('id', 'paid_at', 'created_at', 'updated_at', 'is_paid', 'is_pending')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'order', 'method', 'status')
        }),
        ('Transação', {
            'fields': ('transaction_id', 'amount', 'paid_at')
        }),
        ('Status', {
            'fields': ('is_paid', 'is_pending')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_failed', 'mark_as_refunded']
    
    def mark_as_paid(self, request, queryset):
        """Marca pagamentos como pago"""
        count = 0
        for payment in queryset:
            if payment.mark_as_paid():
                count += 1
        self.message_user(request, f'{count} pagamento(s) marcado(s) como pago(s).')
    mark_as_paid.short_description = 'Marcar como Pago'
    
    def mark_as_failed(self, request, queryset):
        """Marca pagamentos como falhou"""
        count = 0
        for payment in queryset:
            if payment.mark_as_failed():
                count += 1
        self.message_user(request, f'{count} pagamento(s) marcado(s) como falhou(ram).')
    mark_as_failed.short_description = 'Marcar como Falhou'
    
    def mark_as_refunded(self, request, queryset):
        """Marca pagamentos como reembolsado"""
        count = 0
        for payment in queryset:
            if payment.mark_as_refunded():
                count += 1
        self.message_user(request, f'{count} pagamento(s) marcado(s) como reembolsado(s).')
    mark_as_refunded.short_description = 'Marcar como Reembolsado'
