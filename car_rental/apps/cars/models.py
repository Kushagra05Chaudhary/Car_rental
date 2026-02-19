from django.db import models
from django.conf import settings
from django.utils import timezone

class Car(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'owner'}
    )

    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    car_type = models.CharField(max_length=50, default="Sedan")
    location = models.CharField(max_length=100)

    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    seats = models.IntegerField()
    image = models.ImageField(upload_to='car_images/', null=True, blank=True)

    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
