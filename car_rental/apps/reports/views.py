from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import TemplateView, ListView
from django.utils import timezone
from datetime import timedelta
from .services import OwnerRevenueService
from .models import OwnerReport


class OwnerReportMixin(UserPassesTestMixin, LoginRequiredMixin):
    """Mixin to ensure only owners can access reports"""
    login_url = 'login'
    
    def test_func(self):
        """Check if user is owner"""
        return self.request.user.role == 'owner'
    
    def handle_no_permission(self):
        """Redirect if no permission"""
        messages.error(self.request, 'You must be an owner to access this page.')
        return redirect('car_list')


class OwnerEarningsView(OwnerReportMixin, TemplateView):
    """Show owner earnings dashboard"""
    template_name = 'reports/owner_earnings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner = self.request.user
        
        # Get revenue summary
        summary = OwnerRevenueService.get_revenue_summary(owner)
        context['summary'] = summary
        
        # Get monthly earnings
        context['monthly_earnings'] = OwnerRevenueService.get_monthly_earnings(owner, months=6)
        
        # Get top earning cars
        context['top_cars'] = OwnerRevenueService.get_top_earning_cars(owner, limit=5)
        
        return context


class OwnerRevenueReportView(OwnerReportMixin, TemplateView):
    """Detailed revenue report view"""
    template_name = 'reports/owner_revenue_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner = self.request.user
        
        # Total earnings
        context['total_earnings'] = OwnerRevenueService.get_total_earnings(owner)
        
        # Earnings breakdown
        context['completed_count'] = OwnerRevenueService.get_completed_bookings_count(owner)
        context['pending_count'] = OwnerRevenueService.get_pending_bookings_count(owner)
        context['confirmed_count'] = OwnerRevenueService.get_confirmed_bookings_count(owner)
        
        # Monthly data
        monthly = OwnerRevenueService.get_monthly_earnings(owner, months=12)
        context['monthly_earnings'] = monthly
        
        # Get top earning cars
        context['top_cars'] = OwnerRevenueService.get_top_earning_cars(owner, limit=10)
        
        return context


class OwnerReportListView(OwnerReportMixin, ListView):
    """List owner reports"""
    model = OwnerReport
    template_name = 'reports/owner_reports_list.html'
    context_object_name = 'reports'
    paginate_by = 10
    
    def get_queryset(self):
        """Get only reports for current owner"""
        return OwnerReport.objects.filter(owner=self.request.user).order_by('-generated_at')
