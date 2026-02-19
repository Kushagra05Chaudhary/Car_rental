from apps.cars.models import Car
from apps.bookings.models import Booking
from apps.bookings.services import OwnerBookingService
from apps.reports.services import OwnerRevenueService


class DashboardService:
    """Service for dashboard data"""
    
    @staticmethod
    def get_owner_dashboard_data(owner):
        """Get all data needed for owner dashboard"""
        owner_cars = Car.objects.filter(owner=owner)
        
        return {
            'total_cars': owner_cars.count(),
            'active_cars': owner_cars.filter(is_available=True).count(),
            'pending_cars': owner_cars.filter(status='pending').count(),
            'approved_cars': owner_cars.filter(status='approved').count(),
            
            'total_bookings': Booking.objects.filter(car__in=owner_cars).count(),
            'pending_bookings': Booking.objects.filter(car__in=owner_cars, status='pending').count(),
            'confirmed_bookings': Booking.objects.filter(car__in=owner_cars, status='confirmed').count(),
            'completed_bookings': Booking.objects.filter(car__in=owner_cars, status='completed').count(),
            
            'total_earnings': OwnerRevenueService.get_total_earnings(owner),
            
            'recent_bookings': OwnerBookingService.get_owner_bookings(owner)[:5],
        }
