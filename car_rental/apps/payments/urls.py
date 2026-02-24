from django.urls import path
from . import views_razorpay

urlpatterns = [
    # Razorpay Integration (Primary Payment System)
    path('initiate-payment/', views_razorpay.initiate_payment, name='initiate_payment'),
    # Checkout loaded from a Hold (no Booking created yet — user hasn't paid)
    path('razorpay/checkout/hold/<int:hold_id>/', views_razorpay.razorpay_checkout_hold, name='razorpay_checkout_hold'),
    # Legacy / direct booking checkout kept for admin/debug use
    path('razorpay/checkout/<int:booking_id>/', views_razorpay.razorpay_checkout, name='razorpay_checkout'),
    path('success/', views_razorpay.payment_success, name='razorpay_payment_success'),
    path('failure/', views_razorpay.payment_failure, name='razorpay_payment_failure'),
    path('download-invoice/<int:payment_id>/', views_razorpay.download_invoice, name='download_invoice'),
    path('webhook/', views_razorpay.razorpay_webhook, name='razorpay_webhook'),

    # Admin Dashboard
    path('admin/dashboard/', views_razorpay.admin_payments_dashboard, name='admin_payments_dashboard'),
    path('admin/refund/<int:payment_id>/', views_razorpay.admin_refund_payment, name='admin_refund_payment'),

    # User Transactions History
    path('my-transactions/', views_razorpay.user_transactions, name='user_transactions'),
]
