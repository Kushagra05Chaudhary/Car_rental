from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.cars.models import Car
from django.conf import settings


def get_total_earnings(owner):
    """Total confirmed/ongoing/completed earnings for owner."""
    from apps.payments.models import Payment

    owner_cars = Car.objects.filter(owner=owner)
    confirmed_payments = Payment.objects.filter(
        booking__car__in=owner_cars,
        booking__status__in=['confirmed', 'ongoing', 'completed'],
        status='completed',
    )
    total = confirmed_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    return total


def get_monthly_earnings(owner, months=12):
    """Return a dict of month-label → earnings for the last N months."""
    owner_cars = Car.objects.filter(owner=owner)
    earnings_by_month = {}
    for i in range(months):
        month_start = timezone.now().date().replace(day=1)
        month_start = month_start - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        month_key = month_start.strftime('%B %Y')
        earnings = Payment.objects.filter(
            booking__car__in=owner_cars,
            booking__start_date__gte=month_start,
            booking__start_date__lte=month_end,
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        earnings_by_month[month_key] = float(earnings)
    return dict(reversed(list(earnings_by_month.items())))


def get_completed_bookings_count(owner):
    """Count completed bookings for owner."""
    owner_cars = Car.objects.filter(owner=owner)
    return Booking.objects.filter(car__in=owner_cars, status='completed').count()


def get_pending_bookings_count(owner):
    """Count pending bookings for owner."""
    owner_cars = Car.objects.filter(owner=owner)
    return Booking.objects.filter(car__in=owner_cars, status='pending').count()


def get_confirmed_bookings_count(owner):
    """Count confirmed bookings for owner."""
    owner_cars = Car.objects.filter(owner=owner)
    return Booking.objects.filter(car__in=owner_cars, status='confirmed').count()


def get_revenue_summary(owner):
    """Return complete revenue summary dict for owner."""
    from decimal import Decimal
    owner_cars = Car.objects.filter(owner=owner)
    all_bookings = Booking.objects.filter(car__in=owner_cars)
    completed_earnings = Payment.objects.filter(
        booking__car__in=owner_cars,
        status='completed'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    pending_payments = Payment.objects.filter(
        booking__car__in=owner_cars,
        status='pending'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    commission_rate = getattr(settings, 'PLATFORM_COMMISSION_RATE', 0.1)
    commission_total = completed_earnings * Decimal(str(commission_rate))
    net_earnings = completed_earnings - commission_total
    return {
        'total_earnings': float(completed_earnings),
        'pending_earnings': float(pending_payments),
        'commission_total': float(commission_total),
        'net_earnings': float(net_earnings),
        'total_bookings': all_bookings.count(),
        'completed_bookings': all_bookings.filter(status='completed').count(),
        'pending_bookings': all_bookings.filter(status='pending').count(),
        'confirmed_bookings': all_bookings.filter(status='confirmed').count(),
        'cancelled_bookings': all_bookings.filter(status='cancelled').count(),
        'total_cars': owner_cars.count(),
        'active_cars': owner_cars.filter(is_available=True).count(),
    }


def get_top_earning_cars(owner, limit=5):
    """Return top-N owner cars ordered by total completed payment amount."""
    owner_cars = Car.objects.filter(owner=owner)
    car_totals = (
        Payment.objects.filter(booking__car__in=owner_cars, status='completed')
        .values('booking__car')
        .annotate(total_earned=Sum('amount'))
        .order_by('-total_earned')[:limit]
    )
    top_cars = []
    for entry in car_totals:
        car_id = entry['booking__car']
        try:
            car = owner_cars.get(id=car_id)
            car.total_earned = entry['total_earned']
            top_cars.append(car)
        except Car.DoesNotExist:
            pass
    return top_cars
