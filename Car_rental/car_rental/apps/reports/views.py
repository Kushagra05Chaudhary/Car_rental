from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import TemplateView, ListView
from .services import (
    get_revenue_summary, get_monthly_earnings, get_top_earning_cars,
    get_total_earnings, get_completed_bookings_count,
    get_pending_bookings_count, get_confirmed_bookings_count,
)
from .models import OwnerReport


class OwnerReportMixin(UserPassesTestMixin, LoginRequiredMixin):
    """Mixin to ensure only owners can access reports"""
    login_url = 'login'
    
    def test_func(self):
        """Check if user is owner and not admin or superuser"""
        if self.request.user.is_superuser or self.request.user.role == 'admin':
            return False
        return self.request.user.role == 'owner'
    
    def handle_no_permission(self):
        """Redirect if no permission"""
        if self.request.user.is_superuser or self.request.user.role == 'admin':
            messages.error(self.request, 'Admins can only access admin features.')
            return redirect('admin_dashboard')
        messages.error(self.request, 'You must be an owner to access this page.')
        return redirect('car_list')


class OwnerEarningsView(OwnerReportMixin, TemplateView):
    """Show owner earnings dashboard"""
    template_name = 'reports/owner_earnings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner = self.request.user
        
        # Get revenue summary
        summary = get_revenue_summary(owner)
        context['summary'] = summary
        
        # Get monthly earnings
        context['monthly_earnings'] = get_monthly_earnings(owner, months=6)
        
        # Get top earning cars
        context['top_cars'] = get_top_earning_cars(owner, limit=5)
        
        return context


class OwnerRevenueReportView(OwnerReportMixin, TemplateView):
    """Detailed revenue report view"""
    template_name = 'reports/owner_revenue_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner = self.request.user
        
        # Total earnings
        context['total_earnings'] = get_total_earnings(owner)
        
        # Earnings breakdown
        context['completed_count'] = get_completed_bookings_count(owner)
        context['pending_count'] = get_pending_bookings_count(owner)
        context['confirmed_count'] = get_confirmed_bookings_count(owner)
        
        # Monthly data
        monthly = get_monthly_earnings(owner, months=12)
        context['monthly_earnings'] = monthly
        context['top_cars'] = get_top_earning_cars(owner, limit=10)
        
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
