from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from apps.accounts.models import CustomUser
from apps.cars.models import Car


# Temporary imports (will work when car/booking models exist)
# from apps.cars.models import Car
# from apps.bookings.models import Booking


@login_required
@role_required('admin')
def admin_dashboard(request):

    context = {
        'total_users': CustomUser.objects.filter(role='user').count(),
        'total_owners': CustomUser.objects.filter(role='owner').count(),
        'total_cars': 0,  # update when Car model ready
        'total_bookings': 0,  # update later
    }

    return render(request, 'dashboard/admin_dashboard.html', context)



@login_required
@role_required('owner')
def owner_dashboard(request):

    owner_cars = Car.objects.filter(owner=request.user)

    context = {
        'owner_cars': owner_cars,
    }

    return render(request, 'dashboard/owner_dashboard.html', context)



@login_required
@role_required('user')
def user_dashboard(request):

    context = {
        'my_bookings': 0,
    }

    return render(request, 'dashboard/user_dashboard.html', context)