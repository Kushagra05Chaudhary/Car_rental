from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
    hold = get_object_or_404(BookingHold, id=hold_id, user=request.user)

    if hold.expires_at < timezone.now():
        hold.delete()
        messages.error(request, 'Your reservation expired. Please try again.')
        return redirect('car_detail', pk=hold.car.id)

    days = (hold.end_date - hold.start_date).days
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
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    return render(request, 'payments/success.html', {
        'booking': booking,
    })


@login_required
def invoice_pdf(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.user != request.user and booking.car.owner != request.user and not request.user.is_superuser:
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