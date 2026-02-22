from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:car_id>/', views.create_booking, name='create_booking'),
    path('api/booked-dates/<int:car_id>/', views.car_booked_dates, name='car_booked_dates'),
    # Owner booking views
    path('owner/list/', views.OwnerBookingListView.as_view(), name='owner_booking_list'),
    path('owner/<int:pk>/', views.OwnerBookingDetailView.as_view(), name='owner_booking_detail'),
    path('owner/<int:pk>/accept/', views.OwnerAcceptBookingView.as_view(), name='accept_booking'),
    path('owner/<int:pk>/reject/', views.OwnerRejectBookingView.as_view(), name='reject_booking'),
    
    # User booking views
    path('list/', views.UserBookingListView.as_view(), name='booking_list'),
    path('<int:pk>/', views.UserBookingDetailView.as_view(), name='user_booking_detail'),
]
