from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from .models import Booking
from apps.payments.models import Payment


class OwnerBookingService:
    """Service for managing owner bookings"""
    
    @staticmethod
    def get_owner_bookings(owner, status=None):
        """Get all bookings for owner's cars"""
        from apps.cars.models import Car
        
        owner_cars = Car.objects.filter(owner=owner)
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
        
        # Create payment record
        if not hasattr(booking, 'payment'):
            Payment.objects.create(
                booking=booking,
                user=booking.user,
                amount=booking.total_price,
                status='pending'
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
    def get_user_bookings(user):
        """Get all bookings for a user"""
        return Booking.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def get_user_active_bookings(user):
        """Get active bookings for a user"""
        return Booking.objects.filter(
            user=user,
            status__in=['pending', 'confirmed']
        ).order_by('-created_at')


class AdminBookingService:
    """Service layer for admin booking controls."""

    @staticmethod
    def get_bookings(status=None, start_date=None, end_date=None, query=None):
        bookings = Booking.objects.select_related('user', 'car', 'car__owner').all().order_by('-created_at')

        if status:
            bookings = bookings.filter(status=status)
        if start_date:
            bookings = bookings.filter(created_at__date__gte=start_date)
        if end_date:
            bookings = bookings.filter(created_at__date__lte=end_date)
        if query:
            bookings = bookings.filter(
                Q(user__username__icontains=query)
                | Q(car__name__icontains=query)
                | Q(car__owner__username__icontains=query)
            )

        return bookings

    @staticmethod
    @transaction.atomic
    def cancel_booking(booking):
        if booking.status in ['cancelled', 'completed']:
            raise ValueError('This booking cannot be cancelled.')

        booking.status = 'cancelled'
        booking.save(update_fields=['status'])
        return booking

    @staticmethod
    def can_refund(booking):
        if not hasattr(booking, 'payment'):
            return False
        return booking.payment.status in ['completed', 'pending', 'failed']
