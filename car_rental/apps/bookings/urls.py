from django.urls import path
from . import views

urlpatterns = [
    # Owner booking views
    path('owner/list/', views.OwnerBookingListView.as_view(), name='owner_booking_list'),
    path('owner/<int:pk>/', views.OwnerBookingDetailView.as_view(), name='owner_booking_detail'),
    path('owner/<int:pk>/accept/', views.OwnerAcceptBookingView.as_view(), name='accept_booking'),
    path('owner/<int:pk>/reject/', views.OwnerRejectBookingView.as_view(), name='reject_booking'),
    
    # User booking views
    path('list/', views.UserBookingListView.as_view(), name='booking_list'),
    path('<int:pk>/', views.UserBookingDetailView.as_view(), name='booking_detail'),

    # Admin booking controls
    path('admin/list/', views.AdminBookingListView.as_view(), name='admin_booking_list'),
    path('admin/<int:pk>/cancel/', views.AdminCancelBookingView.as_view(), name='admin_cancel_booking'),
    path('admin/<int:pk>/refund/', views.AdminRefundBookingView.as_view(), name='admin_refund_booking'),
]
