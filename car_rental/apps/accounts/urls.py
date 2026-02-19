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
    path('resend-otp/', views.resend_registration_otp, name='resend_registration_otp'),
    path('become-owner/', views.become_owner, name='become_owner'),
    
    # Owner profile views
    path('owner/profile/', views.owner_profile_view, name='owner_profile'),
    path('owner/profile/edit/', views.owner_profile_edit_view, name='owner_profile_edit'),
    path('owner/change-password/', views.owner_change_password_view, name='owner_change_password'),

    # Admin owner moderation
    path('admin/owners/', views.AdminOwnerListView.as_view(), name='admin_owner_management'),
    path('admin/owners/<int:pk>/approve/', views.ApproveOwnerView.as_view(), name='admin_approve_owner'),
    path('admin/owners/<int:pk>/reject/', views.RejectOwnerView.as_view(), name='admin_reject_owner'),

    # Admin user management
    path('admin/users/', views.AdminUserManagementView.as_view(), name='admin_user_management'),
    path('admin/users/<int:pk>/toggle-status/', views.AdminUserToggleStatusView.as_view(), name='admin_toggle_user_status'),
]