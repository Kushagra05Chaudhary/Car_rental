"""
Razorpay Payment Service
Handles order creation, payment verification, and refunds
"""
import logging
import hmac
import hashlib
import razorpay
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from .models import Payment, Refund
from apps.bookings.models import Booking

logger = logging.getLogger(__name__)


class RazorpayPaymentService:
    """Handle all Razorpay payment operations"""

    def __init__(self):
        """Initialize Razorpay client"""
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    @transaction.atomic
    def create_order(self, booking_id, amount):
        """Create a Razorpay order for booking_id and return order details."""
        try:
            booking = Booking.objects.get(id=booking_id)
            
            # Amount in paise (multiply by 100)
            amount_paise = int(amount * 100)
            
            # Create order in Razorpay
            order_data = {
                'amount': amount_paise,
                'currency': 'INR',
                'receipt': f'booking_{booking.id}',
                'payment_capture': 1,  # Auto capture
                'notes': {
                    'booking_id': booking.id,
                    'user_email': booking.user.email,
                    'car_name': booking.car.name,
                }
            }
            
            order = self.client.order.create(data=order_data)
            
            # Store order ID in booking
            booking.razorpay_order_id = order['id']
            booking.save(update_fields=['razorpay_order_id'])
            
            # Create Payment record
            Payment.objects.create(
                booking=booking,
                user=booking.user,
                amount=amount,
                status='pending',
                razorpay_order_id=order['id'],
                payment_method='razorpay'
            )
            
            logger.info(f"Order created: {order['id']} for booking {booking.id}")
            
            return {
                'order_id': order['id'],
                'amount': amount,
                'currency': 'INR',
                'key_id': self.key_id,
                'booking_id': booking.id,
            }
            
        except Booking.DoesNotExist:
            logger.error(f"Booking {booking_id} not found")
            raise ValueError(f"Booking {booking_id} not found")
        except Exception as e:
            logger.error(f"Order creation failed: {str(e)}")
            raise

    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """Return True if the Razorpay HMAC-SHA256 signature is valid."""
        try:
            body = f'{razorpay_order_id}|{razorpay_payment_id}'
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.key_secret.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Verify signature
            is_valid = hmac.compare_digest(expected_signature, razorpay_signature)
            
            if not is_valid:
                logger.warning(f"Invalid signature for payment {razorpay_payment_id}")
                
            return is_valid
            
        except Exception as e:
            logger.error(f"Signature verification error: {str(e)}")
            return False

    @transaction.atomic
    def handle_payment_success(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """Verify signature, mark payment completed, and update booking to pending-owner-approval."""
        # Verify signature first
        if not self.verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
            raise ValueError("Payment signature verification failed")
        
        try:
            # Get payment record
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            
            # Update payment record
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = 'completed'
            payment.transaction_id = razorpay_payment_id
            payment.save()

            # Update booking — status stays 'pending' so the owner
            # must explicitly confirm or reject before the car is
            # assigned.  payment_status='paid' records that money was
            # received and the car is now blocked from other bookings.
            booking = payment.booking
            booking.payment_status = 'paid'
            booking.status = 'pending'   # awaiting owner approval
            booking.razorpay_payment_id = razorpay_payment_id
            booking.razorpay_signature = razorpay_signature
            booking.save()
            
            logger.info(f"Payment successful: {razorpay_payment_id} for booking {booking.id}")
            
            return {
                'success': True,
                'payment_id': razorpay_payment_id,
                'booking_id': booking.id,
                'message': 'Payment completed successfully'
            }
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for order {razorpay_order_id}")
            raise ValueError(f"Payment not found for order {razorpay_order_id}")
        except Exception as e:
            logger.error(f"Payment success handling error: {str(e)}")
            raise

    @transaction.atomic
    def handle_payment_failure(self, razorpay_order_id, error_code=None, error_description=None):
        """Mark payment as failed and delete the associated booking."""
        try:
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)

            # Update payment status
            payment.status = 'failed'
            payment.save()

            # Delete the booking — payment was never captured, so the
            # booking should not persist.  The user's Hold is still
            # active and will expire naturally if they abandon.
            booking = payment.booking
            payment.delete()  # must delete Payment first (FK to Booking via OneToOne)
            booking.delete()

            logger.warning(f'Payment failed and booking cleaned up: {razorpay_order_id}')

        except Payment.DoesNotExist:
            logger.error(f'Payment not found for order {razorpay_order_id}')
        except Exception as e:
            logger.error(f'Payment failure handling error: {str(e)}')

    @transaction.atomic
    def create_refund(self, payment_id, reason=None, initiated_by=None):
        """Issue a Razorpay refund for payment_id and return refund details."""
        try:
            payment = Payment.objects.get(id=payment_id)
            
            # Check if payment can be refunded
            if payment.status not in ['completed']:
                raise ValueError(f"Cannot refund payment with status: {payment.status}")
            
            if not payment.razorpay_payment_id:
                raise ValueError("Razorpay payment ID not found")
            
            # Create refund via Razorpay API
            refund_data = {
                'amount': int(payment.amount * 100),  # Amount in paise
                'notes': {
                    'reason': reason or 'No reason provided',
                    'booking_id': payment.booking.id
                }
            }
            
            refund = self.client.payment.refund(
                payment.razorpay_payment_id,
                refund_data
            )
            
            # Create refund record
            refund_obj = Refund.objects.create(
                payment=payment,
                razorpay_refund_id=refund['id'],
                amount=payment.amount,
                status='processed',
                reason=reason,
                initiated_by=initiated_by
            )
            
            # Update payment status
            payment.status = 'refunded'
            payment.save()

            # Update booking status to 'refunded' so the car is
            # released back into the available pool.
            booking = payment.booking
            booking.status = 'refunded'
            booking.save()

            logger.info(f"Refund processed: {refund['id']} for payment {payment.id}")
            
            return {
                'success': True,
                'refund_id': refund['id'],
                'amount': payment.amount,
                'message': 'Refund processed successfully'
            }
            
        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            raise ValueError(f"Payment {payment_id} not found")
        except Exception as e:
            logger.error(f"Refund creation failed: {str(e)}")
            raise

    def verify_webhook_signature(self, webhook_body, webhook_signature):
        """Return True if the webhook HMAC-SHA256 signature matches."""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                webhook_body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, webhook_signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification error: {str(e)}")
            return False

    def fetch_payment_details(self, razorpay_payment_id):
        """Fetch and return payment details from Razorpay API."""
        try:
            payment = self.client.payment.fetch(razorpay_payment_id)
            return payment
        except Exception as e:
            logger.error(f"Failed to fetch payment details: {str(e)}")
            raise
