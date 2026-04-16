from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from transactions.models import Payment

class Command(BaseCommand):
    help = 'Clean up expired pending payments'
    
    def handle(self, *args, **options):
        expiry_time = timezone.now() - timedelta(minutes=5)
        expired_payments = Payment.objects.filter(
            status='pending',
            created_at__lt=expiry_time
        )
        
        count = expired_payments.count()
        for payment in expired_payments:
            payment.status = 'cancelled'
            payment.save()
            payment.order.status = 'pending'
            payment.order.save()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully cancelled {count} expired payments'))