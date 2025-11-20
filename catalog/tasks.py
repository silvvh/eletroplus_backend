from celery import shared_task
from django.utils import timezone
from .models import StockReservation

@shared_task
def expire_old_reservations():
    """Expira reservas antigas"""
    expired_count = StockReservation.objects.filter(
        status='RESERVED',
        expires_at__lt=timezone.now()
    ).update(status='EXPIRED')
    
    return f"Expiraram {expired_count} reservas"
