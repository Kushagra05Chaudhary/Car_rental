from django.db import transaction
from django.utils import timezone
from .models import Booking, BookingHold
from apps.payments.models import Payment
from apps.notifications.services import create_notification


class OwnerBookingService:
    """Service for managing owner bookings"""

    @staticmethod
    def update_completed_bookings_for_cars(cars_queryset):
        """Mark confirmed bookings as completed after end date."""
        today = timezone.now().date()
        bookings = Booking.objects.filter(
            car__in=cars_queryset,
            status='confirmed',
            end_date__lt=today
        )

        for booking in bookings:
            booking.status = 'completed'
            booking.save(update_fields=['status'])

            if hasattr(booking, 'payment') and booking.payment.status != 'completed':
                booking.payment.status = 'completed'
                booking.payment.save(update_fields=['status'])
    
    @staticmethod
    def get_owner_bookings(owner, status=None):
        """Get all bookings for owner's cars"""
        from apps.cars.models import Car
        
        owner_cars = Car.objects.filter(owner=owner)
        OwnerBookingService.update_completed_bookings_for_cars(owner_cars)
        bookings = Booking.objects.filter(car__in=owner_cars)
        
        if status:
            bookings = bookings.filter(status=status)
        
        return bookings.order_by('-created_at')
    
    @staticmethod
    def get_pending_bookings(owner):
        """Get pending bookings for owner"""
        return OwnerBookingService.get_owner_bookings(owner, status='pending')
    
    @staticmethod
    def get_confirmed_bookings(owner):
        """Get confirmed bookings for owner"""
        return OwnerBookingService.get_owner_bookings(owner, status='confirmed')
    
    @staticmethod
    def get_completed_bookings(owner):
        """Get completed bookings for owner"""
        return OwnerBookingService.get_owner_bookings(owner, status='completed')
    
    @staticmethod
    @transaction.atomic
    def accept_booking(booking):
        """Accept a booking"""
        if booking.status != 'pending':
            raise ValueError('Only pending bookings can be accepted.')
        
        # Update booking status
        booking.status = 'confirmed'
        booking.save()
        
        # Ensure payment exists
        if not hasattr(booking, 'payment'):
            Payment.objects.create(
                booking=booking,
                user=booking.user,
                amount=booking.total_price,
                status='completed',
                payment_method='SIMULATED'
            )

        create_notification(
            booking.user,
            'Booking confirmed',
            f"Your booking for {booking.car.name} has been confirmed."
        )
        
        return booking
    
    @staticmethod
    @transaction.atomic
    def reject_booking(booking):
        """Reject a booking"""
        if booking.status != 'pending':
            raise ValueError('Only pending bookings can be rejected.')
        
        booking.status = 'rejected'
        booking.save()

        if hasattr(booking, 'payment') and booking.payment.status == 'completed':
            booking.payment.status = 'refunded'
            booking.payment.save(update_fields=['status'])

        create_notification(
            booking.user,
            'Booking rejected',
            f"Your booking for {booking.car.name} was rejected."
        )
        
        return booking
    
    @staticmethod
    @transaction.atomic
    def cancel_booking(booking):
        """Cancel a booking"""
        if booking.status not in ['pending', 'confirmed']:
            raise ValueError('Only pending/confirmed bookings can be cancelled.')
        
        booking.status = 'cancelled'
        booking.save()
        
        return booking
    
    @staticmethod
    def get_booking_details(booking_id, owner):
        """Get booking details with validation"""
        from apps.cars.models import Car
        
        try:
            booking = Booking.objects.get(id=booking_id)
            
            # Verify owner owns the car
            if booking.car.owner != owner:
                return None
            
            return booking
        except Booking.DoesNotExist:
            return None


class UserBookingService:
    """Service for managing user bookings"""
    
    @staticmethod
    def create_booking(user, car, start_date, end_date):
        """Create a new booking"""
        days = (end_date - start_date).days + 1
        total_price = days * car.price_per_day
        
        booking = Booking.objects.create(
            user=user,
            car=car,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price,
            status='pending'
        )
        
        return booking

    @staticmethod
    def update_completed_bookings_for_user(user):
        """Mark confirmed bookings as completed after end date for user."""
        today = timezone.now().date()
        bookings = Booking.objects.filter(
            user=user,
            status='confirmed',
            end_date__lt=today
        )

        for booking in bookings:
            booking.status = 'completed'
            booking.save(update_fields=['status'])

            if hasattr(booking, 'payment') and booking.payment.status != 'completed':
                booking.payment.status = 'completed'
                booking.payment.save(update_fields=['status'])

    @staticmethod
    def clear_expired_holds():
        """Remove expired booking holds."""
        BookingHold.objects.filter(expires_at__lt=timezone.now()).delete()

    @staticmethod
    def has_conflicts(car, start_date, end_date, exclude_user=None):
        """Check for booking or active hold conflicts."""
        UserBookingService.clear_expired_holds()

        booking_conflict = Booking.objects.filter(
            car=car,
            status__in=['pending', 'confirmed', 'completed'],
            start_date__lt=end_date,
            end_date__gt=start_date
        ).exists()

        if booking_conflict:
            return True

        holds = BookingHold.objects.filter(
            car=car,
            expires_at__gt=timezone.now(),
            start_date__lt=end_date,
            end_date__gt=start_date
        )

        if exclude_user:
            holds = holds.exclude(user=exclude_user)

        return holds.exists()

    @staticmethod
    def create_hold(user, car, start_date, end_date, hold_minutes=5):
        """Create a reservation hold for payment window."""
        UserBookingService.clear_expired_holds()

        BookingHold.objects.filter(user=user, car=car).delete()

        expires_at = timezone.now() + timezone.timedelta(minutes=hold_minutes)
        return BookingHold.objects.create(
            user=user,
            car=car,
            start_date=start_date,
            end_date=end_date,
            expires_at=expires_at
        )
    
    @staticmethod
    def get_user_bookings(user):
        """Get all bookings for a user"""
        UserBookingService.update_completed_bookings_for_user(user)
        return Booking.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def get_user_active_bookings(user):
        """Get active bookings for a user"""
        return Booking.objects.filter(
            user=user,
            status__in=['pending', 'confirmed']
        ).order_by('-created_at')
