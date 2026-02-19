from django.db import models
from apps.bookings.models import Booking


class Payment(models.Model):

    PAYMENT_METHODS = (
        ('RAZORPAY', 'Razorpay'),
        ('STRIPE', 'Stripe'),
        ('COD', 'Cash On Delivery'),
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)

    payment_id = models.CharField(max_length=200, blank=True, null=True)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    is_successful = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.booking.id}"
