from django.urls import path
from . import views

urlpatterns = [
    path('owner/earnings/', views.OwnerEarningsView.as_view(), name='owner_earnings'),
    path('owner/revenue/', views.OwnerRevenueReportView.as_view(), name='owner_revenue_report'),
    path('owner/reports/', views.OwnerReportListView.as_view(), name='owner_reports_list'),
    path('admin/analytics/', views.AdminReportsView.as_view(), name='admin_reports'),
]
