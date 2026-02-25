"""
Payment Views - Razorpay Integration
Master payment flow: booking → order creation → checkout → verification → confirmation
"""
import json
import logging
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction as db_transaction

from apps.bookings.models import Booking, BookingHold
from apps.bookings.services import has_conflicts
from apps.accounts.decorators import role_required
from apps.notifications.services import create_notification
from .models import Payment, Refund
from .services import RazorpayPaymentService
from .utils import generate_invoice_pdf

logger = logging.getLogger(__name__)
payment_service = RazorpayPaymentService()


# ==================== CHECKOUT PAGE ====================

@login_required
def razorpay_checkout_hold(request, hold_id):
    """
    Checkout page driven by a BookingHold.
    No Booking record exists yet — it is only created when the user
    actually clicks Pay (handled inside initiate_payment).
    """
    if request.user.role == 'admin':
        return redirect('admin_dashboard')

    try:
        hold = BookingHold.objects.get(id=hold_id, user=request.user)
    except BookingHold.DoesNotExist:
        messages.error(request, 'Your reservation session was not found. Please select dates again.')
        return redirect('car_list')

    if hold.expires_at < timezone.now():
        car_id = hold.car.id
        hold.delete()
        messages.error(request, 'Your reservation expired. Please select dates again.')
        return redirect('car_detail', pk=car_id)

    days = (hold.end_date - hold.start_date).days + 1
    subtotal = days * hold.car.price_per_day
    gst = subtotal * Decimal('0.18')
    total_price = subtotal  # GST is informational only for now

    user_phone = getattr(request.user, 'phone', '') or ''

    context = {
        'hold': hold,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'days': days,
        'subtotal': subtotal,
        'gst': gst,
        'total_price': total_price,
        'user_phone': user_phone,
    }
    return render(request, 'payments/razorpay_checkout.html', context)


@login_required
def razorpay_checkout(request, booking_id):
    """Legacy checkout from an existing Booking (admin/debug use)."""
    if request.user.role == 'admin':
        return redirect('admin_dashboard')

    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found')
        return redirect('car_list')

    days = (booking.end_date - booking.start_date).days + 1
    subtotal = booking.total_price
    gst = subtotal * Decimal('0.18')

    context = {
        'booking': booking,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'days': days,
        'subtotal': subtotal,
        'gst': gst,
    }
    return render(request, 'payments/razorpay_checkout.html', context)


# ==================== BOOKING & PAYMENT INITIALIZATION ====================

@login_required
@require_http_methods(["POST"])
def initiate_payment(request):
    """
    Called when the user clicks "Pay" on the checkout page.

    Accepts a hold_id (no Booking exists yet).  Creates the Booking record
    atomically with the Razorpay order so that:
      - If the user never reached this point, no Booking is in the DB.
      - If payment ultimately fails, payment_failure deletes the Booking.
      - The Hold keeps protecting the dates until payment_success.
    """
    if request.user.role == 'admin':
        return JsonResponse({'error': 'Admins cannot make bookings'}, status=403)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    hold_id = payload.get('hold_id')
    if not hold_id:
        return JsonResponse({'error': 'hold_id required'}, status=400)

    try:
        hold = BookingHold.objects.get(id=hold_id, user=request.user)
    except BookingHold.DoesNotExist:
        return JsonResponse({'error': 'Reservation not found or expired. Please select dates again.'}, status=404)

    if hold.expires_at < timezone.now():
        hold.delete()
        return JsonResponse({'error': 'Reservation expired. Please select dates again.'}, status=400)

    # Final conflict check right before creating the booking
    if has_conflicts(hold.car, hold.start_date, hold.end_date, exclude_user=request.user):
        hold.delete()
        return JsonResponse({'error': 'These dates are no longer available. Please choose different dates.'}, status=409)

    try:
        # Create Booking now (payment_status='pending' until Razorpay confirms)
        from decimal import Decimal as D
        days = (hold.end_date - hold.start_date).days + 1
        total_price = D(days) * hold.car.price_per_day

        booking = Booking.objects.create(
            user=request.user,
            car=hold.car,
            start_date=hold.start_date,
            end_date=hold.end_date,
            total_price=total_price,
            status='pending',
            payment_status='pending',
        )

        # Create Razorpay order (also creates Payment record)
        order_details = payment_service.create_order(booking.id, total_price)

        return JsonResponse({
            'success': True,
            'order_id': order_details['order_id'],
            'amount': float(order_details['amount']),
            'key_id': order_details['key_id'],
            'booking_id': booking.id,
        })

    except Exception as e:
        logger.error(f'Order creation failed: {str(e)}')
        # Clean up the booking we just created so it does not linger
        try:
            booking.delete()
        except Exception:
            pass
        return JsonResponse({'error': f'Failed to create order: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def payment_success(request):
    """
    Verify payment signature and confirm booking
    Called after successful Razorpay payment
    """
    if request.user.role == 'admin':
        return JsonResponse({'error': 'Admins cannot make payments'}, status=403)

    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return JsonResponse({'error': 'Missing payment details'}, status=400)

        # Verify payment and update booking
        result = payment_service.handle_payment_success(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        )

        # Get booking for notifications
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        booking = payment.booking

        # Delete the hold now that payment is confirmed
        BookingHold.objects.filter(
            user=booking.user,
            car=booking.car,
            start_date=booking.start_date,
            end_date=booking.end_date,
        ).delete()

        # Send notifications
        create_notification(
            booking.user,
            '✓ Payment Confirmed',
            f'Payment received for {booking.car.name}. Awaiting owner approval.'
        )
        create_notification(
            booking.car.owner,
            '📋 New Booking Request',
            f'New booking request for {booking.car.name} from {booking.user.first_name or booking.user.username}. Please confirm or reject.'
        )

        # Use Django reverse() for proper URL generation
        redirect_url = reverse('user_booking_detail', kwargs={'pk': booking.id})

        return JsonResponse({
            'success': True,
            'message': 'Payment verified successfully',
            'booking_id': booking.id,
            'redirect_url': redirect_url
        })

    except ValueError as e:
        logger.warning(f"Payment verification failed: {str(e)}")
        return JsonResponse({'error': f'Payment verification failed: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f"Payment success handling error: {str(e)}")
        return JsonResponse({'error': f'Error processing payment: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def payment_failure(request):
    """
    Handle payment failure — clean up booking and redirect user to retry.
    Called after a failed Razorpay payment.
    """
    if request.user.role == 'admin':
        return JsonResponse({'error': 'Admins cannot make payments'}, status=403)

    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get('razorpay_order_id')
        error_code = data.get('error_code')
        error_description = data.get('error_description')

        # Fetch car_id and user BEFORE the service deletes the records,
        # so we can notify the user and build the retry redirect URL.
        try:
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            car_id = payment.booking.car.id
            booking_user = payment.booking.user
            car_name = payment.booking.car.name
        except Payment.DoesNotExist:
            # Already cleaned up by a previous call or webhook
            return JsonResponse({'success': True, 'message': 'Already cleaned up'})

        # Notify user before deletion
        create_notification(
            booking_user,
            '✗ Payment Failed',
            f'Payment failed for {car_name}. Please try again.',
        )

        # Delegate cleanup to the service (deletes Payment + Booking atomically)
        payment_service.handle_payment_failure(razorpay_order_id, error_code, error_description)

        retry_url = reverse('car_detail', kwargs={'pk': car_id})
        return JsonResponse({
            'success': True,
            'message': 'Failure recorded',
            'redirect_url': retry_url,
        })

    except Exception as e:
        logger.error(f'Payment failure handling error: {str(e)}')
        return JsonResponse({'error': f'Error processing failure: {str(e)}'}, status=500)


# ==================== PAYMENT HISTORY & INVOICES ====================

@login_required
def user_transactions(request):
    """User's own transaction/payment history"""
    if request.user.role in ('admin',):
        return redirect('admin_dashboard')

    # Get user's payments
    payments = Payment.objects.filter(user=request.user).select_related('booking__car')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['pending', 'completed', 'failed', 'refunded']:
        payments = payments.filter(status=status_filter)

    # Calculate totals
    total_spent = payments.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_refunded = payments.filter(status='refunded').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    net_spent = Decimal(total_spent) - Decimal(total_refunded)

    context = {
        'payments': payments,
        'total_spent': total_spent,
        'total_refunded': total_refunded,
        'net_spent': net_spent,
        'status_filter': status_filter,
    }

    return render(request, 'payments/user_transactions.html', context)


@login_required
def download_invoice(request, payment_id):
    """Download invoice PDF for a payment"""
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user)
        
        if payment.status != 'completed':
            messages.error(request, 'Invoice available only for completed payments')
            return redirect('user_transactions')

        # Generate PDF
        pdf_bytes = generate_invoice_pdf(payment)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{payment.razorpay_payment_id}.pdf"'
        
        return response

    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found')
        return redirect('user_transactions')


# ==================== ADMIN PAYMENT MANAGEMENT ====================

@login_required
@role_required('admin')
def admin_payments_dashboard(request):
    """Admin dashboard for all payments"""
    
    # Get all payments
    payments = Payment.objects.select_related('booking__car', 'booking__user').all()

    # Filters
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    method_filter = request.GET.get('method')

    if status_filter and status_filter in ['pending', 'completed', 'failed', 'refunded']:
        payments = payments.filter(status=status_filter)
    
    if date_from:
        payments = payments.filter(created_at__gte=date_from)
    
    if date_to:
        payments = payments.filter(created_at__lte=date_to)
    
    if method_filter:
        payments = payments.filter(payment_method=method_filter)

    # Calculate totals
    total_revenue = payments.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_refunded = payments.filter(status='refunded').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    net_revenue = Decimal(total_revenue) - Decimal(total_refunded)

    # Status breakdown
    status_counts = {
        'pending': payments.filter(status='pending').count(),
        'completed': payments.filter(status='completed').count(),
        'failed': payments.filter(status='failed').count(),
        'refunded': payments.filter(status='refunded').count(),
    }

    context = {
        'payments': payments[:100],  # Paginate if needed
        'total_revenue': total_revenue,
        'total_refunded': total_refunded,
        'net_revenue': net_revenue,
        'status_counts': status_counts,
        'total_payments': payments.count(),
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'method_filter': method_filter,
    }

    return render(request, 'payments/admin_payments_dashboard.html', context)


@login_required
@role_required('admin')
@require_http_methods(["POST"])
def admin_refund_payment(request, payment_id):
    """Admin initiates refund"""
    try:
        payment = Payment.objects.get(id=payment_id)
        reason = request.POST.get('reason', '')

        # Create refund
        refund_result = payment_service.create_refund(
            payment_id,
            reason=reason,
            initiated_by=request.user
        )

        messages.success(request, f"Refund processed: {refund_result['refund_id']}")
        
        # Notify user
        create_notification(
            payment.booking.user,
            '💰 Refund Processed',
            f'Your refund of ₹{payment.amount} has been processed.'
        )

        return redirect('admin_payments_dashboard')

    except ValueError as e:
        messages.error(request, str(e))
        return redirect('admin_payments_dashboard')
    except Exception as e:
        logger.error(f"Refund error: {str(e)}")
        messages.error(request, 'Error processing refund')
        return redirect('admin_payments_dashboard')


# ==================== WEBHOOKS ====================

@csrf_exempt
@require_http_methods(["POST"])
def razorpay_webhook(request):
    """
    Razorpay webhook endpoint
    Handle payment.captured, payment.failed, refund.processed events
    """
    try:
        # Get webhook signature
        webhook_signature = request.headers.get('X-Razorpay-Signature', '')
        webhook_body = request.body.decode('utf-8')

        # Verify signature
        if not payment_service.verify_webhook_signature(webhook_body, webhook_signature):
            logger.warning("Invalid webhook signature")
            return JsonResponse({'error': 'Invalid signature'}, status=403)

        # Parse event
        event = json.loads(webhook_body)
        event_type = event.get('event')

        logger.info(f"Webhook received: {event_type}")

        if event_type == 'payment.captured':
            handle_payment_captured(event)
        elif event_type == 'payment.failed':
            handle_payment_failed(event)
        elif event_type == 'refund.processed':
            handle_refund_processed(event)

        return JsonResponse({'status': 'ok'})

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@db_transaction.atomic
def handle_payment_captured(event):
    """Handle payment.captured webhook event"""
    try:
        payment_data = event.get('payload', {}).get('payment', {}).get('entity', {})
        razorpay_payment_id = payment_data.get('id')
        razorpay_order_id = payment_data.get('order_id')

        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        
        if payment.status == 'pending':
            payment.razorpay_payment_id = razorpay_payment_id
            payment.status = 'completed'
            payment.transaction_id = razorpay_payment_id
            payment.save()

            # Update booking — status stays 'pending' (awaiting owner approval)
            booking = payment.booking
            booking.payment_status = 'paid'
            booking.status = 'pending'
            booking.razorpay_payment_id = razorpay_payment_id
            booking.save()

            logger.info(f'Webhook: Payment captured {razorpay_payment_id}')

    except Exception as e:
        logger.error(f"Error handling payment.captured: {str(e)}")


@db_transaction.atomic
def handle_payment_failed(event):
    """Handle payment.failed webhook event"""
    try:
        payment_data = event.get('payload', {}).get('payment', {}).get('entity', {})
        razorpay_order_id = payment_data.get('order_id')

        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        payment.status = 'failed'
        payment.save()

        booking = payment.booking
        booking.payment_status = 'failed'
        booking.save()

        logger.warning(f"Webhook: Payment failed for order {razorpay_order_id}")

    except Exception as e:
        logger.error(f"Error handling payment.failed: {str(e)}")


@db_transaction.atomic
def handle_refund_processed(event):
    """Handle refund.processed webhook event"""
    try:
        refund_data = event.get('payload', {}).get('refund', {}).get('entity', {})
        razorpay_refund_id = refund_data.get('id')

        refund = Refund.objects.get(razorpay_refund_id=razorpay_refund_id)
        refund.status = 'processed'
        refund.save()

        logger.info(f"Webhook: Refund processed {razorpay_refund_id}")

    except Exception as e:
        logger.error(f"Error handling refund.processed: {str(e)}")
