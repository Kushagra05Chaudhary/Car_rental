from django.urls import path
from . import views

urlpatterns = [
  path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
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

]
