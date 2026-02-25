from django.db import models
from apps.cars.models import Car
from apps.bookings.models import Booking
from apps.bookings.services import get_owner_bookings
from apps.reports.services import get_total_earnings


def get_owner_dashboard_data(owner):
    """Return all data needed for the owner dashboard."""
    owner_cars = Car.objects.filter(owner=owner)

    return {
        'total_cars':    owner_cars.count(),
        'active_cars':   owner_cars.filter(is_available=True).count(),
        'pending_cars':  owner_cars.filter(status='pending').count(),
        'approved_cars': owner_cars.filter(status='approved').count(),

        'total_bookings':     Booking.objects.filter(car__in=owner_cars).count(),
        'pending_bookings':   Booking.objects.filter(
            car__in=owner_cars, status='pending', payment_status='paid'
        ).count(),
        'confirmed_bookings': Booking.objects.filter(car__in=owner_cars, status='confirmed').count(),
        'completed_bookings': Booking.objects.filter(car__in=owner_cars, status='completed').count(),

        'total_earnings':  get_total_earnings(owner),
        'pending_earnings': Booking.objects.filter(
            car__in=owner_cars, status='pending', payment_status='paid'
        ).aggregate(total=models.Sum('total_price'))['total'] or 0,

        'recent_bookings': get_owner_bookings(owner)[:5],
    }
