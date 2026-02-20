from django.urls import path
from . import views

urlpatterns = [
	path('checkout/<int:hold_id>/', views.payment_checkout, name='payment_checkout'),
	path('success/<int:booking_id>/', views.payment_success, name='payment_success'),
	path('invoice/<int:booking_id>/', views.invoice_pdf, name='invoice_pdf'),
	path('my-transactions/', views.user_transactions, name='user_transactions'),
]
