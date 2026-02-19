from apps.accounts.models import OwnerRequest
from apps.bookings.models import Booking
from apps.cars.models import Car
from apps.payments.models import Payment


def admin_sidebar_data(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'admin_sidebar': {}}

    if not (user.is_superuser or getattr(user, 'role', None) == 'admin'):
        return {'admin_sidebar': {}}

    return {
        'admin_sidebar': {
            'pending_owners': OwnerRequest.objects.filter(status='pending').count(),
            'pending_cars': Car.objects.filter(status='pending').count(),
            'pending_bookings': Booking.objects.filter(status='pending').count(),
            'failed_payments': Payment.objects.filter(status='failed').count(),
        }
    }
