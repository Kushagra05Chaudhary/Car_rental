from django.db import models
from django.conf import settings
from apps.cars.models import Car


class Booking(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('AWAITING_OWNER_APPROVAL', 'Awaiting Owner Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )

    PAYMENT_STATUS = (
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)

    start_date = models.DateField()
    end_date = models.DateField()

    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='UNPAID')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.car.name}"

    def clean(self):
        from django.core.exceptions import ValidationError
    
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")
    
        if (self.end_date - self.start_date).days < 1:
            raise ValidationError("Booking duration must be at least 1 day.")
    
        overlapping_bookings = Booking.objects.filter(
            car=self.car,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date,
            status__in=['PENDING', 'AWAITING_OWNER_APPROVAL', 'APPROVED']
        )
    
        if self.pk:
            overlapping_bookings = overlapping_bookings.exclude(pk=self.pk)
    
        if overlapping_bookings.exists():
            raise ValidationError("This car is already booked for the selected dates.")
