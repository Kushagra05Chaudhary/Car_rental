from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncMonth
from apps.accounts.models import CustomUser
from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.cars.models import Car


class OwnerRevenueService:
    """Service for calculating owner earnings and revenue"""
    
    @staticmethod
    def get_total_earnings(owner):
        """Get total earnings for owner from completed bookings"""
        from apps.payments.models import Payment
        
        owner_cars = Car.objects.filter(owner=owner)
        completed_payments = Payment.objects.filter(
            booking__car__in=owner_cars,
            status='completed'
        )
        
        total = completed_payments.aggregate(Sum('amount'))['amount__sum'] or 0
        return total
    
    @staticmethod
    def get_monthly_earnings(owner, months=12):
        """Get monthly earnings for owner (last N months)"""
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
    
    @staticmethod
    def get_completed_bookings_count(owner):
        """Get total completed bookings for owner"""
        owner_cars = Car.objects.filter(owner=owner)
        return Booking.objects.filter(
            car__in=owner_cars,
            status='completed'
        ).count()
    
    @staticmethod
    def get_pending_bookings_count(owner):
        """Get total pending bookings for owner"""
        owner_cars = Car.objects.filter(owner=owner)
        return Booking.objects.filter(
            car__in=owner_cars,
            status='pending'
        ).count()
    
    @staticmethod
    def get_confirmed_bookings_count(owner):
        """Get total confirmed bookings for owner"""
        owner_cars = Car.objects.filter(owner=owner)
        return Booking.objects.filter(
            car__in=owner_cars,
            status='confirmed'
        ).count()
    
    @staticmethod
    def get_revenue_summary(owner):
        """Get complete revenue summary for owner"""
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
        
        return {
            'total_earnings': float(completed_earnings),
            'pending_earnings': float(pending_payments),
            'total_bookings': all_bookings.count(),
            'completed_bookings': all_bookings.filter(status='completed').count(),
            'pending_bookings': all_bookings.filter(status='pending').count(),
            'confirmed_bookings': all_bookings.filter(status='confirmed').count(),
            'cancelled_bookings': all_bookings.filter(status='cancelled').count(),
            'total_cars': owner_cars.count(),
            'active_cars': owner_cars.filter(is_available=True).count(),
        }
    
    @staticmethod
    def get_top_earning_cars(owner, limit=5):
        """Get top earning cars for owner"""
        owner_cars = Car.objects.filter(owner=owner)
        
        top_cars = owner_cars.annotate(
            total_earned=Sum(
                'bookings__payment__amount',
                filter=Q(bookings__payment__status='completed')
            )
        ).order_by('-total_earned')[:limit]
        
        return top_cars


class AdminReportService:
    """Service layer for admin-level reports and analytics."""

    @staticmethod
    def get_summary(start_date=None, end_date=None):
        payments = Payment.objects.filter(status='completed')
        bookings = Booking.objects.all()

        if start_date:
            payments = payments.filter(created_at__date__gte=start_date)
            bookings = bookings.filter(created_at__date__gte=start_date)
        if end_date:
            payments = payments.filter(created_at__date__lte=end_date)
            bookings = bookings.filter(created_at__date__lte=end_date)

        return {
            'revenue': payments.aggregate(total=Sum('amount'))['total'] or 0,
            'bookings': bookings.count(),
            'completed_bookings': bookings.filter(status='completed').count(),
            'active_owners': CustomUser.objects.filter(role='owner').count(),
        }

    @staticmethod
    def get_booking_trends(start_date=None, end_date=None):
        bookings = Booking.objects.all()
        if start_date:
            bookings = bookings.filter(created_at__date__gte=start_date)
        if end_date:
            bookings = bookings.filter(created_at__date__lte=end_date)

        data = bookings.annotate(month=TruncMonth('created_at')).values('month').annotate(total=Count('id')).order_by('month')
        return {
            'labels': [item['month'].strftime('%b %Y') for item in data],
            'data': [item['total'] for item in data],
        }

    @staticmethod
    def get_owner_performance(limit=10):
        return (
            CustomUser.objects.filter(role='owner')
            .annotate(
                total_cars=Count('car', distinct=True),
                total_bookings=Count('car__bookings', distinct=True),
                total_revenue=Sum(
                    'car__bookings__payment__amount',
                    filter=Q(car__bookings__payment__status='completed')
                ),
            )
            .order_by('-total_revenue')[:limit]
        )

    @staticmethod
    def get_top_performing_cars(limit=10):
        return (
            Car.objects.select_related('owner')
            .annotate(
                total_bookings=Count('bookings', distinct=True),
                total_revenue=Sum(
                    'bookings__payment__amount',
                    filter=Q(bookings__payment__status='completed')
                ),
            )
            .order_by('-total_revenue')[:limit]
        )
