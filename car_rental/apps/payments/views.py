from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from apps.bookings.models import Booking
from .models import Payment


@login_required
def payment_success(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    # Prevent double payment
    if booking.payment_status == "PAID":
        return redirect("user_bookings")

    # Create payment record
    Payment.objects.create(
        booking=booking,
        method="RAZORPAY",
        amount=booking.total_price,
        is_successful=True
    )

    # Update booking
    booking.payment_status = "PAID"
    booking.status = "AWAITING_OWNER_APPROVAL"
    booking.save()

    return redirect("user_bookings")




def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.is_successful = True
    payment.save()

    booking = payment.booking
    booking.payment_status = 'PAID'
    booking.status = 'AWAITING_OWNER_APPROVAL'
    booking.save()

    return redirect('user_bookings')