from django.db import transaction
from django.utils import timezone
from .models import Booking, BookingHold
from apps.payments.models import Payment
from apps.notifications.services import create_notification


class OwnerBookingService:
    """Service for managing owner bookings"""

    @staticmethod
    def auto_transition_bookings_for_cars(cars_queryset):
        """
        Auto-advance booking statuses based on today's date:

        - confirmed  → ongoing   when start_date <= today <= end_date
        - ongoing    → completed when end_date < today
        - confirmed  → completed when end_date < today (safety net)
        """
        today = timezone.now().date()

        # confirmed → ongoing (rental has started)
        started = Booking.objects.filter(
            car__in=cars_queryset,
            status='confirmed',
            start_date__lte=today,
            end_date__gte=today,
        )
        started.update(status='ongoing')

        # confirmed or ongoing → completed (rental has ended)
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

    @staticmethod
    def get_owner_bookings(owner, status=None):
        """Get all bookings for owner's cars"""
        from apps.cars.models import Car

        owner_cars = Car.objects.filter(owner=owner)
        OwnerBookingService.auto_transition_bookings_for_cars(owner_cars)
        bookings = Booking.objects.filter(car__in=owner_cars)

        if status:
            bookings = bookings.filter(status=status)

        return bookings.order_by('-created_at')

    @staticmethod
    def get_pending_bookings(owner):
        return OwnerBookingService.get_owner_bookings(owner, status='pending')

    @staticmethod
    def get_confirmed_bookings(owner):
        return OwnerBookingService.get_owner_bookings(owner, status='confirmed')

    @staticmethod
    def get_completed_bookings(owner):
        return OwnerBookingService.get_owner_bookings(owner, status='completed')

    @staticmethod
    @transaction.atomic
    def accept_booking(booking):
        """Accept a pending booking — car becomes blocked for those dates."""
        if booking.status != 'pending':
            raise ValueError('Only pending bookings can be accepted.')

        booking.status = 'confirmed'
        booking.save()

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

    @staticmethod
    @transaction.atomic
    def reject_booking(booking):
        """
        Reject a pending booking.

        If the user already paid (payment_status='paid'), the payment is
        automatically refunded via Razorpay so the car is released back to
        the available pool with status='refunded'.  Otherwise the booking
        is simply marked 'rejected'.
        """
        if booking.status != 'pending':
            raise ValueError('Only pending bookings can be rejected.')

        # Trigger Razorpay refund when the user already paid
        if booking.payment_status == 'paid' and hasattr(booking, 'payment'):
            try:
                from apps.payments.services import RazorpayPaymentService
                payment_service = RazorpayPaymentService()
                payment_service.create_refund(
                    booking.payment.id,
                    reason='Booking rejected by owner',
                )
                # create_refund already sets booking.status = 'refunded'
            except Exception as e:
                # Fall back to manual mark if Razorpay call fails
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
            + ("A refund has been initiated." if booking.payment_status == 'paid' else ""),
        )
        return booking

    @staticmethod
    @transaction.atomic
    def cancel_booking(booking):
        """Cancel a booking — car is released back to pool."""
        if booking.status not in ['pending', 'confirmed']:
            raise ValueError('Only pending/confirmed bookings can be cancelled.')

        booking.status = 'cancelled'
        booking.save()
        return booking

    @staticmethod
    def get_booking_details(booking_id, owner):
        """Get booking details, validated against owner."""
        try:
            booking = Booking.objects.get(id=booking_id)
            if booking.car.owner != owner:
                return None
            return booking
        except Booking.DoesNotExist:
            return None


class UserBookingService:
    """Service for managing user bookings"""

    @staticmethod
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

    @staticmethod
    def auto_transition_bookings_for_user(user):
        """
        Auto-advance booking statuses for a user's bookings.

        - confirmed  → ongoing   (start_date reached, end_date not yet passed)
        - confirmed / ongoing → completed (end_date passed)
        """
        today = timezone.now().date()

        Booking.objects.filter(
            user=user,
            status='confirmed',
            start_date__lte=today,
            end_date__gte=today,
        ).update(status='ongoing')

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

    @staticmethod
    def clear_stale_bookings():
        """
        Delete bookings that were created during initiate_payment but whose
        Razorpay payment was never captured (user closed the browser, network
        error, etc.).  A booking is considered stale when:
          - payment_status is still 'pending'  (money never received)
          - created more than BOOKING_HOLD_MINUTES + 5 minutes ago
        """
        from django.conf import settings
        hold_minutes = getattr(settings, 'BOOKING_HOLD_MINUTES', 10)
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

    @staticmethod
    def clear_expired_holds():
        """Remove expired booking holds."""
        BookingHold.objects.filter(expires_at__lt=timezone.now()).delete()

    @staticmethod
    def has_conflicts(car, start_date, end_date, exclude_user=None):
        """
        Check whether any CONFIRMED or ONGOING booking (plus active holds)
        overlaps with [start_date, end_date] for this car.

        NOTE: PENDING, COMPLETED, CANCELLED, REJECTED and REFUNDED bookings
        do NOT block the car — only CONFIRMED and ONGOING ones do,
        plus PENDING bookings where payment_status='paid'.
        """
        UserBookingService.clear_expired_holds()
        UserBookingService.clear_stale_bookings()

        # Booking conflict — only block on active statuses
        if Booking.has_conflict(car, start_date, end_date):
            return True

        # Hold conflict
        holds = BookingHold.objects.filter(
            car=car,
            expires_at__gt=timezone.now(),
            start_date__lt=end_date,
            end_date__gt=start_date,
        )
        if exclude_user:
            holds = holds.exclude(user=exclude_user)

        return holds.exists()

    @staticmethod
    def create_hold(user, car, start_date, end_date, hold_minutes=15):
        """Create a reservation hold for the payment window."""
        UserBookingService.clear_expired_holds()
        BookingHold.objects.filter(user=user, car=car).delete()

        expires_at = timezone.now() + timezone.timedelta(minutes=hold_minutes)
        return BookingHold.objects.create(
            user=user,
            car=car,
            start_date=start_date,
            end_date=end_date,
            expires_at=expires_at,
        )

    @staticmethod
    def get_user_bookings(user):
        """Get all bookings for a user, with auto status transitions."""
        UserBookingService.auto_transition_bookings_for_user(user)
        return Booking.objects.filter(user=user).order_by('-created_at')

    @staticmethod
    def get_user_active_bookings(user):
        """Get active (confirmed / ongoing) bookings for a user."""
        return Booking.objects.filter(
            user=user,
            status__in=['pending', 'confirmed', 'ongoing'],
        ).order_by('-created_at')
