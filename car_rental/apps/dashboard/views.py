from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from apps.accounts.models import CustomUser, OwnerRequest
from apps.cars.models import Car
from apps.bookings.models import Booking
from .services import DashboardService

@login_required
@role_required('admin')
def admin_dashboard(request):
    """Admin dashboard view"""
    context = {
        'total_users': CustomUser.objects.filter(role='user').count(),
        'total_owners': CustomUser.objects.filter(role='owner').count(),
        'total_cars': Car.objects.count(),
        'pending_cars': Car.objects.filter(status='pending').count(),
        'pending_owner_requests': OwnerRequest.objects.filter(status='pending').count(),
        'approved_cars': Car.objects.filter(status='approved').count(),
        'total_bookings': Booking.objects.count(),
        'pending_bookings': Booking.objects.filter(status='pending').count(),
        'completed_bookings': Booking.objects.filter(status='completed').count(),
    }

    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
@role_required('admin')
def admin_car_approval(request):

    cars = Car.objects.filter(status='pending')

    return render(request, 'dashboard/admin_car_approval.html', {
        'cars': cars
    })

@login_required
@role_required('admin')
def approve_car(request, pk):
    car = Car.objects.get(pk=pk)
    car.status = 'approved'
    car.save()
    return redirect('admin_car_approval')

@login_required
@role_required('admin')
def reject_car(request, pk):
    car = Car.objects.get(pk=pk)
    car.status = 'rejected'
    car.save()
    return redirect('admin_car_approval')

@login_required
@role_required('admin')
def admin_owner_requests(request):

    requests = OwnerRequest.objects.filter(status='pending')

    return render(request, 'dashboard/admin_owner_requests.html', {
        'requests': requests
    })
@login_required
@role_required('admin')
def approve_owner(request, pk):
    req = OwnerRequest.objects.get(pk=pk)
    req.status = 'approved'
    req.save()

    user = req.user
    user.role = 'owner'
    user.save()

    return redirect('admin_owner_requests')


@login_required
@role_required('admin')
def reject_owner(request, pk):
    req = OwnerRequest.objects.get(pk=pk)
    req.status = 'rejected'
    req.save()

    return redirect('admin_owner_requests')
    
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
