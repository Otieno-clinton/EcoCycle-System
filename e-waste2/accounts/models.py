


from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password, check_password

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('producer', 'E-Waste Producer'),
        ('collector', 'Collector & Recycler'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='producer')
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class CollectionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('assigned', 'Assigned'),
        ('collected', 'Collected'),
        ('recycled', 'Recycled'),
        ('landfill', 'Sent to Landfill'),
        ('rejected', 'Rejected'),
    ]
    
    WASTE_TYPES = [
        ('electronics', 'Electronics'),
        ('batteries', 'Batteries'),
        ('appliances', 'Appliances'),
        ('other', 'Other'),
    ]
    
    DISPOSITION_CHOICES = [
        ('recycled', 'Recycled'),
        ('landfill', 'Sent to Landfill'),
        ('other', 'Other Disposition'),
    ]
    
    producer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPES)
    quantity = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    collection_date = models.DateField(null=True, blank=True)
    collector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments')
    admin_notes = models.TextField(blank=True)
    # New fields for recycling
    final_disposition = models.CharField(max_length=20, choices=DISPOSITION_CHOICES, null=True, blank=True)
    recycling_notes = models.TextField(blank=True)
    recycling_date = models.DateField(null=True, blank=True)
    actual_quantity = models.PositiveIntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"Request #{self.id} - {self.get_waste_type_display()} ({self.get_status_display()})"
    





    # Add to your models.py
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    request = models.ForeignKey(CollectionRequest, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, null=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    admin_approved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Payment for Request #{self.request.id} - KES {self.amount}"