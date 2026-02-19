from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from apps.accounts.decorators import role_required
from apps.bookings.models import Booking
from .services import DashboardService, AdminDashboardService


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('admin'), name='dispatch')
class AdminDashboardView(TemplateView):
    template_name = 'dashboard/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = AdminDashboardService.get_dashboard_stats()
        context.update(stats)
        context['revenue_chart'] = AdminDashboardService.get_monthly_revenue_chart()
        context['booking_status_chart'] = AdminDashboardService.get_booking_status_chart()
        context['recent_activities'] = AdminDashboardService.get_recent_activities()
        return context

@login_required
@role_required('admin')
def admin_dashboard(request):
    """Backward-compatible endpoint for existing function-based route."""
    return AdminDashboardView.as_view()(request)

@login_required
@role_required('admin')
def admin_car_approval(request):
    return redirect('admin_car_list')

@login_required
@role_required('admin')
def approve_car(request, pk):
    return redirect('admin_car_list')

@login_required
@role_required('admin')
def reject_car(request, pk):
    return redirect('admin_car_list')

@login_required
@role_required('admin')
def admin_owner_requests(request):
    return redirect('admin_owner_management')
@login_required
@role_required('admin')
def approve_owner(request, pk):
    return redirect('admin_owner_management')


@login_required
@role_required('admin')
def reject_owner(request, pk):
    return redirect('admin_owner_management')
    
@login_required
@role_required('owner')
def owner_dashboard(request):
    """Owner dashboard view with comprehensive statistics"""
    
    # Get all dashboard data using service
    dashboard_data = DashboardService.get_owner_dashboard_data(request.user)
    
    return render(request, 'dashboard/owner_dashboard.html', dashboard_data)


@login_required
@role_required('user')
def user_dashboard(request):
    """User dashboard view"""
    user_bookings = Booking.objects.filter(user=request.user)
    
    context = {
        'my_bookings': user_bookings.count(),
        'active_bookings': user_bookings.filter(status__in=['pending', 'confirmed']).count(),
        'completed_bookings': user_bookings.filter(status='completed').count(),
        'recent_bookings': user_bookings.order_by('-created_at')[:5],
    }
    
    return render(request, 'dashboard/user_dashboard.html', context)