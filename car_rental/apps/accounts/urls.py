from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect/', views.dashboard_redirect, name='dashboard_redirect'),
    # path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('otp-login/', views.send_otp, name='otp_login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    
]