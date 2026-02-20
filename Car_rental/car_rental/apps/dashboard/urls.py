from django.urls import path
from . import views

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('user/', views.user_dashboard, name='user_dashboard'),
      # Car Approval Section
    path('admin/cars/', views.admin_car_approval, name='admin_car_approval'),
    path('admin/cars/approve/<int:pk>/', views.approve_car, name='approve_car'),
    path('admin/cars/reject/<int:pk>/', views.reject_car, name='reject_car'),

    # Owner Request Section
    path('admin/owners/', views.admin_owner_requests, name='admin_owner_requests'),
    path('admin/owners/approve/<int:pk>/', views.approve_owner, name='approve_owner'),
    path('admin/owners/reject/<int:pk>/', views.reject_owner, name='reject_owner'),
    
    # User Management Section
    path('admin/users/', views.admin_users_management, name='admin_users_management'),
    path('admin/users/<int:user_id>/block/', views.block_user, name='block_user'),
    path('admin/users/<int:user_id>/unblock/', views.unblock_user, name='unblock_user'),
    path('admin/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('admin/users/<int:user_id>/remove-owner/', views.remove_owner, name='remove_owner'),
    
    # Reports Section
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('admin/reports/download/', views.download_report, name='download_report'),

    # Transactions Section
    path('admin/transactions/', views.admin_transactions, name='admin_transactions'),

    # All Cars Section
    path('admin/all-cars/', views.admin_all_cars, name='admin_all_cars'),
    path('admin/all-cars/<int:pk>/toggle-availability/', views.admin_toggle_car_availability, name='admin_toggle_car_availability'),
    path('admin/all-cars/<int:pk>/delete/', views.admin_delete_car, name='admin_delete_car'),

    # All Bookings Section
    path('admin/bookings/', views.admin_all_bookings, name='admin_all_bookings'),
]
