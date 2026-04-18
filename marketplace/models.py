from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'

class Produce(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('piece', 'Piece'),
        ('bunch', 'Bunch'),
        ('sack', 'Sack'),
        ('tray', 'Tray'),
        ('litre', 'Litre'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold_out', 'Sold Out'),
        ('low_stock', 'Low Stock'),
        ('discontinued', 'Discontinued'),
    ]
    
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='produce_list')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='produce/', null=True, blank=True)
    video_url = models.URLField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.farmer.username}"
    
    @property
    def total_value(self):
        from decimal import Decimal
        return Decimal(str(self.quantity)) * Decimal(str(self.price))
    
    @property
    def is_low_stock(self):
        return self.quantity < 50 and self.status == 'available'
    
    def save(self, *args, **kwargs):
        from decimal import Decimal
        if self.quantity <= Decimal('0'):
            self.status = 'sold_out'
        elif self.quantity < Decimal('50'):
            self.status = 'low_stock'
        elif self.status == 'sold_out' and self.quantity > Decimal('0'):
            self.status = 'available'
        super().save(*args, **kwargs)

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    produce = models.ForeignKey(Produce, on_delete=models.CASCADE, related_name='orders')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_address = models.TextField()
    notes = models.TextField(blank=True)
    
    # New fields for payment and tracking
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    mpesa_receipt = models.CharField(max_length=50, blank=True, null=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    courier_name = models.CharField(max_length=100, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        from decimal import Decimal
        if not self.order_number:
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        quantity_decimal = Decimal(str(self.quantity))
        price_decimal = Decimal(str(self.produce.price))
        self.total_price = quantity_decimal * price_decimal
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.order_number} - {self.buyer.username}"