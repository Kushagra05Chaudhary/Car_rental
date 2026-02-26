from django.db import transaction
from django.utils import timezone
from .models import Booking, BookingHold
from apps.payments.models import Payment
from apps.notifications.services import create_notification


# ============ OWNER BOOKING FUNCTIONS ============

def auto_transition_bookings_for_cars(cars_queryset):
    """Auto-advance booking statuses based on today's date."""
    today = timezone.now().date()

    # Move confirmed bookings to ongoing when the rental has started
    Booking.objects.filter(
        car__in=cars_queryset,
        status='confirmed',
        start_date__lte=today,
        end_date__gte=today,
    ).update(status='ongoing')

    # Move confirmed/ongoing bookings to completed when the rental has ended
    ended = Booking.objects.filter(
        car__in=cars_queryset,
        status__in=['confirmed', 'ongoing'],
        end_date__lt=today,
    )
    for booking in ended:
        booking.status = 'completed'
        booking.save(update_fields=['status', 'updated_at'])
        if hasattr(booking, 'payment') and booking.payment.status != 'completed':
            booking.payment.status = 'completed'
            booking.payment.save(update_fields=['status'])


def get_owner_bookings(owner, status=None):
    """Get all bookings for an owner's cars, with auto status transitions."""
    from apps.cars.models import Car

    owner_cars = Car.objects.filter(owner=owner)
    auto_transition_bookings_for_cars(owner_cars)

    bookings = Booking.objects.filter(car__in=owner_cars).select_related(
        'user', 'car', 'car__owner'
    )

    if status:
        bookings = bookings.filter(status=status)

    return bookings.order_by('-created_at')


def get_pending_bookings(owner):
    """Get pending bookings for an owner."""
    return get_owner_bookings(owner, status='pending')


def get_confirmed_bookings(owner):
    """Get confirmed bookings for an owner."""
    return get_owner_bookings(owner, status='confirmed')


def get_completed_bookings(owner):
    """Get completed bookings for an owner."""
    return get_owner_bookings(owner, status='completed')


@transaction.atomic
def accept_booking(booking):
    """Accept a pending booking — car becomes blocked for those dates."""
    if booking.status != 'pending':
        raise ValueError('Only pending bookings can be accepted.')

    booking.status = 'confirmed'
    booking.save()

    # Create a simulated payment record if none exists (e.g. admin-created bookings)
    if not hasattr(booking, 'payment'):
        Payment.objects.create(
            booking=booking,
            user=booking.user,
            amount=booking.total_price,
            status='completed',
            payment_method='SIMULATED',
        )

    create_notification(
        booking.user,
        'Booking confirmed',
        f"Your booking for {booking.car.name} has been confirmed.",
    )
    return booking


@transaction.atomic
def reject_booking(booking):
    """
    Reject a pending booking.
    If the user already paid, trigger a Razorpay refund.
    Otherwise, simply mark the booking as rejected.
    """
    if booking.status != 'pending':
        raise ValueError('Only pending bookings can be rejected.')

    refund_initiated = False
    if booking.payment_status == 'paid' and hasattr(booking, 'payment'):
        try:
            from apps.payments.services import RazorpayPaymentService
            payment_service = RazorpayPaymentService()
            payment_service.create_refund(
                booking.payment.id,
                reason='Booking rejected by owner',
            )
            # create_refund already sets booking.status and booking.payment_status = 'refunded'
            refund_initiated = True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'Refund failed for booking {booking.id}: {e}')
            booking.status = 'rejected'
            booking.save()
    else:
        booking.status = 'rejected'
        booking.save()

    create_notification(
        booking.user,
        'Booking rejected',
        f"Your booking for {booking.car.name} was rejected by the owner. "
        + ("A refund has been initiated." if refund_initiated else ""),
    )
    return booking


@transaction.atomic
def cancel_booking(booking):
    """Cancel a booking — car is released back to pool."""
    if booking.status not in ['pending', 'confirmed']:
        raise ValueError('Only pending/confirmed bookings can be cancelled.')

    booking.status = 'cancelled'
    booking.save()
    return booking


def get_booking_details(booking_id, owner):
    """Get a single booking, only if it belongs to this owner."""
    try:
        booking = Booking.objects.get(id=booking_id)
        if booking.car.owner != owner:
            return None
        return booking
    except Booking.DoesNotExist:
        return None


# ============ USER BOOKING FUNCTIONS ============

def create_booking(user, car, start_date, end_date):
    """Create a new booking after verifying no date conflict."""
    if Booking.has_conflict(car, start_date, end_date):
        raise ValueError(
            "This car is already booked for the selected dates. Please choose different dates."
        )
    days = (end_date - start_date).days + 1
    total_price = days * car.price_per_day

    return Booking.objects.create(
        user=user,
        car=car,
        start_date=start_date,
        end_date=end_date,
        total_price=total_price,
        status='pending',
    )


def auto_transition_bookings_for_user(user):
    """Auto-advance booking statuses for a user's bookings."""
    today = timezone.now().date()

    # Move confirmed bookings to ongoing when the rental has started
    Booking.objects.filter(
        user=user,
        status='confirmed',
        start_date__lte=today,
        end_date__gte=today,
    ).update(status='ongoing')

    # Move confirmed/ongoing bookings to completed when the rental has ended
    ended = Booking.objects.filter(
        user=user,
        status__in=['confirmed', 'ongoing'],
        end_date__lt=today,
    )
    for booking in ended:
        booking.status = 'completed'
        booking.save(update_fields=['status', 'updated_at'])
        if hasattr(booking, 'payment') and booking.payment.status != 'completed':
            booking.payment.status = 'completed'
            booking.payment.save(update_fields=['status'])


def clear_stale_bookings():
    """Delete bookings where Razorpay payment was never captured."""
    from django.conf import settings
    hold_minutes = getattr(settings, 'BOOKING_HOLD_MINUTES', 10)
    # A booking is stale if it's still pending payment and older than the hold window
    cutoff = timezone.now() - timezone.timedelta(minutes=hold_minutes + 5)
    stale = Booking.objects.filter(
        payment_status='pending',
        status='pending',
        created_at__lt=cutoff,
    )
    count = stale.count()
    if count:
        stale.delete()
    return count


def clear_expired_holds():
    """Remove expired booking holds."""
    BookingHold.objects.filter(expires_at__lt=timezone.now()).delete()


def has_conflicts(car, start_date, end_date, exclude_user=None):
    """Check whether any blocking booking or active hold overlaps the date range."""
    clear_expired_holds()
    clear_stale_bookings()

    # Check booking conflicts first
    if Booking.has_conflict(car, start_date, end_date):
        return True

    # Check hold conflicts
    holds = BookingHold.objects.filter(
        car=car,
        expires_at__gt=timezone.now(),
        start_date__lt=end_date,
        end_date__gt=start_date,
    )
    if exclude_user:
        holds = holds.exclude(user=exclude_user)

    return holds.exists()


def create_hold(user, car, start_date, end_date, hold_minutes=15):
    """Create a reservation hold for the payment window."""
    clear_expired_holds()
    # Remove any existing hold this user has on this car
    BookingHold.objects.filter(user=user, car=car).delete()

    expires_at = timezone.now() + timezone.timedelta(minutes=hold_minutes)
    return BookingHold.objects.create(
        user=user,
        car=car,
        start_date=start_date,
        end_date=end_date,
        expires_at=expires_at,
    )


def get_user_bookings(user):
    """Get all bookings for a user, with auto status transitions."""
    auto_transition_bookings_for_user(user)
    return Booking.objects.filter(user=user).select_related(
        'car', 'car__owner'
    ).order_by('-created_at')


def get_user_active_bookings(user):
    """Get active (pending/confirmed/ongoing) bookings for a user."""
    return Booking.objects.filter(
        user=user,
        status__in=['pending', 'confirmed', 'ongoing'],
    ).order_by('-created_at')
