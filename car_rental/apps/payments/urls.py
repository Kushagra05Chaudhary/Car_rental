from django.urls import path
from . import views

urlpatterns = [
	path('success/<int:booking_id>/', views.payment_success, name='payment_success'),
]
