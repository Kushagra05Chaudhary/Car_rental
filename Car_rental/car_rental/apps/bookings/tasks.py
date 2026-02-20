# Email helper tasks for the bookings app
from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(email, otp):
    """Send OTP verification email."""
    send_mail(
        'Your OTP Code - CarRent',
        f'Your OTP verification code is: {otp}\n\nThis code will expire shortly.',
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=True,
    )


def send_booking_confirmation_email(booking):
    """Send booking confirmation email to the user."""
    send_mail(
        'Booking Confirmed - CarRent',
        f'Your booking for {booking.car.name} from {booking.start_date} to {booking.end_date} has been confirmed.',
        settings.EMAIL_HOST_USER,
        [booking.user.email],
        fail_silently=True,
    )


def send_payment_confirmation_email(payment):
    """Send payment confirmation email to the user."""
    send_mail(
        'Payment Received - CarRent',
        f'Your payment of ₹{payment.amount} has been received.',
        settings.EMAIL_HOST_USER,
        [payment.user.email],
        fail_silently=True,
    )
