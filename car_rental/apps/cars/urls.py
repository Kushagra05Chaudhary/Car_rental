from django.urls import path
from . import views

urlpatterns = [
    # Public views
    path('', views.car_list, name='car_list'),
    path('<int:pk>/', views.car_detail, name='car_detail'),
    
    # Owner views
    path('owner/list/', views.OwnerCarListView.as_view(), name='owner_car_list'),
    path('owner/add/', views.OwnerCarCreateView.as_view(), name='owner_add_car'),
    path('owner/<int:pk>/edit/', views.OwnerCarUpdateView.as_view(), name='owner_edit_car'),
    path('owner/<int:pk>/delete/', views.OwnerCarDeleteView.as_view(), name='owner_delete_car'),
    path('owner/<int:pk>/toggle-availability/', views.OwnerCarToggleAvailabilityView.as_view(), name='toggle_availability'),

    # Admin moderation views
    path('admin/list/', views.AdminCarListView.as_view(), name='admin_car_list'),
    path('admin/<int:pk>/toggle-availability/', views.AdminCarAvailabilityToggleView.as_view(), name='admin_toggle_car_availability'),
    path('admin/<int:pk>/toggle-featured/', views.AdminCarFeatureToggleView.as_view(), name='admin_toggle_car_featured'),
    path('admin/bulk-action/', views.AdminCarBulkActionView.as_view(), name='admin_car_bulk_action'),
]
