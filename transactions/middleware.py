from django.utils.deprecation import MiddlewareMixin
from .views import check_expired_payments

class PaymentCleanupMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Run cleanup every 10 requests (to avoid performance issues)
        import random
        if random.randint(1, 10) == 1:
            check_expired_payments(request)