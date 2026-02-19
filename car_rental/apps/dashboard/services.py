from decimal import Decimal
from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.accounts.models import CustomUser, OwnerRequest
from apps.bookings.models import Booking
from apps.cars.models import Car
from apps.bookings.services import OwnerBookingService
from apps.payments.models import Payment
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


class AdminDashboardService:
    """Service for admin dashboard analytics."""

    @staticmethod
    def get_dashboard_stats():
        total_revenue = Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0')

        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = Payment.objects.filter(
            status='completed',
            created_at__gte=current_month_start,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return {
            'total_users': CustomUser.objects.filter(role='user').count(),
            'total_owners': CustomUser.objects.filter(role='owner').count(),
            'total_cars': Car.objects.count(),
            'active_cars': Car.objects.filter(is_available=True, status='approved').count(),
            'total_bookings': Booking.objects.count(),
            'pending_bookings': Booking.objects.filter(status='pending').count(),
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'pending_owner_requests': OwnerRequest.objects.filter(status='pending').count(),
            'pending_cars': Car.objects.filter(status='pending').count(),
        }

    @staticmethod
    def get_monthly_revenue_chart(months=6):
        now = timezone.now()
        start = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=32 * (months - 1))).replace(day=1)

        monthly_data = (
            Payment.objects.filter(status='completed', created_at__gte=start)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

        revenue_map = {entry['month'].strftime('%b %Y'): float(entry['total']) for entry in monthly_data}
        labels = []
        data = []

        for index in range(months):
            month_date = (start + timedelta(days=32 * index)).replace(day=1)
            key = month_date.strftime('%b %Y')
            labels.append(key)
            data.append(revenue_map.get(key, 0.0))

        return {'labels': labels, 'data': data}

    @staticmethod
    def get_booking_status_chart():
        status_counts = Booking.objects.values('status').annotate(total=Count('id')).order_by('status')
        return {
            'labels': [entry['status'].title() for entry in status_counts],
            'data': [entry['total'] for entry in status_counts],
        }

    @staticmethod
    def get_recent_activities(limit=12):
        activities = []

        for booking in Booking.objects.select_related('user', 'car').order_by('-updated_at')[:limit]:
            activities.append({
                'type': 'Booking',
                'title': f"{booking.user.username} • {booking.car.name}",
                'status': booking.status,
                'timestamp': booking.updated_at,
                'amount': booking.total_price,
            })

        for payment in Payment.objects.select_related('user', 'booking').order_by('-updated_at')[:limit]:
            activities.append({
                'type': 'Payment',
                'title': f"{payment.user.username} • #{payment.booking_id}",
                'status': payment.status,
                'timestamp': payment.updated_at,
                'amount': payment.amount,
            })

        for request in OwnerRequest.objects.select_related('user').order_by('-created_at')[:limit]:
            activities.append({
                'type': 'Owner Request',
                'title': request.user.username,
                'status': request.status,
                'timestamp': request.created_at,
                'amount': None,
            })

        activities.sort(key=lambda item: item['timestamp'], reverse=True)
        return activities[:limit]
