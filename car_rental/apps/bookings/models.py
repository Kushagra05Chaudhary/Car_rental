from django.db import models
from django.conf import settings
from apps.cars.models import Car
from django.utils import timezone


# ──────────────────────────────────────────────
# Booking Model
# ──────────────────────────────────────────────

class Booking(models.Model):

    # Statuses that actively block a car's availability
    # Note: pending+paid also blocks the car (user paid, owner hasn't decided yet)
    BLOCKING_STATUSES = ('confirmed', 'ongoing')  # simple tuple for direct filter use

    # Statuses that release a car back to the available pool
    RELEASING_STATUSES = ('completed', 'cancelled', 'rejected', 'refunded')

    STATUS_CHOICES = (
        ('pending',   'Pending'),    # Paid, awaiting owner approval
        ('confirmed', 'Confirmed'),  # Owner approved — car is blocked
        ('ongoing',   'Ongoing'),    # Rental in progress — car is blocked
        ('completed', 'Completed'),  # Rental finished — car is free
        ('cancelled', 'Cancelled'),  # User cancelled — car is free
        ('rejected',  'Rejected'),   # Owner rejected — car is free
        ('refunded',  'Refunded'),   # Payment refunded — car is free
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending',  'Pending'),
        ('paid',     'Paid'),
        ('failed',   'Failed'),
        ('refunded', 'Refunded'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings'
    )
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='bookings')

    start_date = models.DateField()
    end_date   = models.DateField()

    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price   = models.DecimalField(max_digits=10, decimal_places=2)

    # Razorpay integration
    razorpay_order_id   = models.CharField(max_length=100, blank=True, null=True, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature  = models.CharField(max_length=255, blank=True, null=True)
    payment_status      = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Speeds up the car-availability overlap query
            models.Index(fields=['car', 'status', 'start_date', 'end_date'],
                         name='booking_car_status_dates_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.car.name} [{self.status}]"

    # ── Helpers ──────────────────────────────────────

    def get_days(self):
        """Number of rental days (inclusive)."""
        return (self.end_date - self.start_date).days + 1

    @property
    def is_blocking(self):
        """True when this booking blocks the car from other renters."""
        return (
            self.status in ('confirmed', 'ongoing') or
            (self.status == 'pending' and self.payment_status == 'paid')
        )

    @classmethod
    def has_conflict(cls, car, start_date, end_date, exclude_booking_id=None):
        """Return True if the date range overlaps any blocking booking for this car."""
        # Two date ranges overlap when: start1 < end2 AND end1 > start2

        # Check confirmed/ongoing bookings that overlap
        confirmed_overlap = cls.objects.filter(
            car=car,
            status__in=['confirmed', 'ongoing'],
            start_date__lt=end_date,
            end_date__gt=start_date,
        )

        # Check paid-pending bookings that overlap (money received, car is committed)
        paid_pending_overlap = cls.objects.filter(
            car=car,
            status='pending',
            payment_status='paid',
            start_date__lt=end_date,
            end_date__gt=start_date,
        )

        if exclude_booking_id:
            confirmed_overlap = confirmed_overlap.exclude(pk=exclude_booking_id)
            paid_pending_overlap = paid_pending_overlap.exclude(pk=exclude_booking_id)

        return confirmed_overlap.exists() or paid_pending_overlap.exists()

    @classmethod
    def get_available_cars(cls, start_date, end_date, base_queryset=None):
        """Return cars with no blocking booking overlapping the date range."""
        from apps.cars.models import Car as CarModel

        # Use the provided queryset or fall back to all approved, available cars
        qs = base_queryset if base_queryset is not None else CarModel.objects.filter(
            status='approved', is_available=True
        )

        # Cars blocked by confirmed/ongoing bookings that overlap the dates
        confirmed_blocked = cls.objects.filter(
            status__in=['confirmed', 'ongoing'],
            start_date__lt=end_date,
            end_date__gt=start_date,
        ).values_list('car_id', flat=True)

        # Cars blocked by paid-pending bookings that overlap the dates
        paid_pending_blocked = cls.objects.filter(
            status='pending',
            payment_status='paid',
            start_date__lt=end_date,
            end_date__gt=start_date,
        ).values_list('car_id', flat=True)

        # Combine both sets of blocked car IDs and exclude them
        blocked_car_ids = set(confirmed_blocked) | set(paid_pending_blocked)
        return qs.exclude(id__in=blocked_car_ids)


# ──────────────────────────────────────────────
# BookingHold — temporary lock during payment
# ──────────────────────────────────────────────

class BookingHold(models.Model):
    """Temporary reservation lock while user completes payment."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='booking_holds'
    )
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='booking_holds')

    start_date = models.DateField()
    end_date   = models.DateField()

    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Hold — {self.user.username} — {self.car.name}"
