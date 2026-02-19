from django.db import transaction
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth

from apps.payments.models import Payment


class PaymentAdminService:
    """Admin operations for payments."""

    @staticmethod
    @transaction.atomic
    def refund_payment(payment):
        if payment.status == 'refunded':
            raise ValueError('Payment is already refunded.')

        payment.status = 'refunded'
        payment.save(update_fields=['status'])

        booking = payment.booking
        if booking.status not in ['cancelled', 'rejected']:
            booking.status = 'cancelled'
            booking.save(update_fields=['status'])

        return payment


class PaymentAnalyticsService:
    """Payment analytics data for admin pages."""

    @staticmethod
    def get_summary(period='monthly'):
        payments = Payment.objects.all()
        completed = payments.filter(status='completed')

        return {
            'total_transactions': payments.count(),
            'failed_transactions': payments.filter(status='failed').count(),
            'refunded_transactions': payments.filter(status='refunded').count(),
            'total_revenue': completed.aggregate(total=Sum('amount'))['total'] or 0,
        }

    @staticmethod
    def get_revenue_chart_data():
        qs = (
            Payment.objects.filter(status='completed')
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )
        return {
            'labels': [row['month'].strftime('%b %Y') for row in qs],
            'data': [float(row['total']) for row in qs],
        }

    @staticmethod
    def get_status_breakdown():
        qs = Payment.objects.values('status').annotate(total=Count('id')).order_by('status')
        return {
            'labels': [row['status'].title() for row in qs],
            'data': [row['total'] for row in qs],
        }
