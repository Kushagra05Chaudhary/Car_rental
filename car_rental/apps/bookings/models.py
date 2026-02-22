from django.db import models
from django.db.models import Q
from django.conf import settings
from apps.cars.models import Car
from django.utils import timezone


# ──────────────────────────────────────────────
# Custom QuerySet
# ──────────────────────────────────────────────

class BookingQuerySet(models.QuerySet):
    """Reusable queryset helpers for booking lookups."""

    @staticmethod
    def _blocking_q():
        """
        A Q object that matches bookings which should block a car:
          - status confirmed or ongoing  (owner approved / in progress)
          - status pending AND payment_status paid  (money received,
            awaiting owner decision — car is already committed)
        """
        return (
            Q(status__in=['confirmed', 'ongoing']) |
            Q(status='pending', payment_status='paid')
        )

    def active(self):
        """Bookings that block the car for their date range."""
        return self.filter(self._blocking_q())

    def overlapping(self, start_date, end_date):
        """
        Standard date-overlap filter using Allen's interval algebra:
        two ranges [A,B] and [C,D] overlap when A < D and B > C.
        """
        return self.filter(
            start_date__lt=end_date,
            end_date__gt=start_date,
        )

    def blocking_for_dates(self, start_date, end_date):
        """Active bookings whose date range overlaps [start_date, end_date]."""
        return self.active().overlapping(start_date, end_date)


class BookingManager(models.Manager):
    def get_queryset(self):
        return BookingQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def overlapping(self, start_date, end_date):
        return self.get_queryset().overlapping(start_date, end_date)

    def blocking_for_dates(self, start_date, end_date):
        return self.get_queryset().blocking_for_dates(start_date, end_date)


# ──────────────────────────────────────────────
# Booking Model
# ──────────────────────────────────────────────

class Booking(models.Model):

    # Statuses that actively block a car's availability
    # Note: pending+paid also blocks — see BookingQuerySet._blocking_q()
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

    objects = BookingManager()

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
        """
        Return True if [start_date, end_date) overlaps with any
        CONFIRMED or ONGOING booking for this car.

        Pass exclude_booking_id to ignore a specific booking (useful
        when editing an existing booking).
        """
        qs = cls.objects.blocking_for_dates(start_date, end_date).filter(car=car)
        if exclude_booking_id:
            qs = qs.exclude(pk=exclude_booking_id)
        return qs.exists()

    @classmethod
    def get_available_cars(cls, start_date, end_date, base_queryset=None):
        """
        Return a Car queryset containing only cars that have NO
        blocking booking overlapping [start_date, end_date).

        Usage:
            available = Booking.get_available_cars(start, end)
        """
        from apps.cars.models import Car as CarModel

        qs = base_queryset if base_queryset is not None else CarModel.objects.filter(
            status='approved', is_available=True
        )

        # IDs of cars that are blocked for this date range
        blocked_car_ids = (
            cls.objects
            .blocking_for_dates(start_date, end_date)
            .values_list('car_id', flat=True)
            .distinct()
        )

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
