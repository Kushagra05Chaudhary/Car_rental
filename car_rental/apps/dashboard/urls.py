from django.urls import path
from . import views

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('user/', views.user_dashboard, name='user_dashboard'),
]
