from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from apps.bookings.models import Booking, BookingHold
from apps.bookings.services import UserBookingService
from apps.bookings.tasks import send_booking_confirmation_email, send_payment_confirmation_email
from apps.notifications.services import create_notification
from .models import Payment


@login_required
def payment_checkout(request, hold_id):
    if request.user.role == 'admin':
        messages.error(request, 'Admins can only access admin features.')
        return redirect('admin_dashboard')

    try:
        hold = BookingHold.objects.get(id=hold_id, user=request.user)
    except BookingHold.DoesNotExist:
        messages.error(request, 'Your reservation session has expired or is no longer valid. Please select dates again.')
        return redirect('car_list')

    if hold.expires_at < timezone.now():
        car_id = hold.car.id
        hold.delete()
        messages.error(request, 'Your reservation timed out. Please select dates again.')
        return redirect('car_detail', pk=car_id)

    days = (hold.end_date - hold.start_date).days + 1
    total_price = days * hold.car.price_per_day

    if request.method == 'POST':
        booking = UserBookingService.create_booking(
            request.user,
            hold.car,
            hold.start_date,
            hold.end_date
        )

        Payment.objects.create(
            booking=booking,
            user=request.user,
            amount=total_price,
            status='completed',
            payment_method='SIMULATED',
            transaction_id=f"SIM-{booking.id}-{int(timezone.now().timestamp())}"
        )

        hold.delete()

        # Send async emails
        send_payment_confirmation_email(booking.payment)
        send_booking_confirmation_email(booking)

        create_notification(
            booking.user,
            'Payment received',
            f"Your payment for {booking.car.name} was received. Awaiting owner approval."
        )
        create_notification(
            booking.car.owner,
            'New booking request',
            f"New booking request for {booking.car.name} from {booking.user.username}."
        )

        messages.success(request, 'Payment successful. Booking request sent.')
        return redirect('payment_success', booking_id=booking.id)

    return render(request, 'payments/checkout.html', {
        'hold': hold,
        'days': days,
        'total_price': total_price,
    })


@login_required
def payment_success(request, booking_id):
    if request.user.is_superuser or request.user.role == 'admin':
        messages.error(request, 'Admins can only access admin features.')
        return redirect('admin_dashboard')

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    return render(request, 'payments/success.html', {
        'booking': booking,
    })


@login_required
def user_transactions(request):
    """User's own transaction history"""
    if request.user.role in ('admin',) or request.user.is_superuser:
        return redirect('admin_dashboard')

    status_filter = request.GET.get('status', '')

    payments = Payment.objects.select_related('booking__car').filter(user=request.user)

    if status_filter:
        payments = payments.filter(status=status_filter)

    payments = payments.order_by('-created_at')

    from decimal import Decimal
    totals = Payment.objects.filter(user=request.user)
    total_spent     = totals.filter(status='completed').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    total_refunded  = totals.filter(status='refunded').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    net_spent       = total_spent - total_refunded

    context = {
        'payments': payments,
        'total_transactions': totals.count(),
        'completed_count':    totals.filter(status='completed').count(),
        'pending_count':      totals.filter(status='pending').count(),
        'refunded_count':     totals.filter(status='refunded').count(),
        'total_spent':    total_spent,
        'total_refunded': total_refunded,
        'net_spent':      net_spent,
        'status_filter':  status_filter,
    }
    return render(request, 'payments/user_transactions.html', context)


@login_required
def invoice_pdf(request, booking_id):
    if request.user.is_superuser or request.user.role == 'admin':
        messages.error(request, 'Admins can only access admin features.')
        return redirect('admin_dashboard')

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.user != request.user and booking.car.owner != request.user:
        raise Http404

    payment = getattr(booking, 'payment', None)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{booking.id}.pdf"'

    pdf = canvas.Canvas(response, pagesize=LETTER)
    y = 750

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Invoice")
    y -= 30

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Invoice ID: INV-{booking.id}")
    y -= 20
    pdf.drawString(50, y, f"Date: {timezone.now().date()}")
    y -= 30

    pdf.drawString(50, y, f"Car: {booking.car.name}")
    y -= 20
    pdf.drawString(50, y, f"Renter: {booking.user.username}")
    y -= 20
    pdf.drawString(50, y, f"Dates: {booking.start_date} to {booking.end_date}")
    y -= 20
    pdf.drawString(50, y, f"Total Amount: {booking.total_price}")
    y -= 30

    if payment:
        pdf.drawString(50, y, f"Payment Status: {payment.status}")
        y -= 20
        if payment.transaction_id:
            pdf.drawString(50, y, f"Transaction ID: {payment.transaction_id}")
            y -= 20

    pdf.showPage()
    pdf.save()

    return response