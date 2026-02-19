from django.urls import path
from . import views

urlpatterns = [
    path("my-bookings/", views.user_bookings, name="user_bookings"),
]
