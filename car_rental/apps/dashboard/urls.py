from django.urls import path
from . import views

urlpatterns = [
    path("owner-bookings/", views.owner_bookings, name="owner_bookings"),
    path("approve/<int:booking_id>/", views.approve_booking, name="approve_booking"),
    path("reject/<int:booking_id>/", views.reject_booking, name="reject_booking"),
]
