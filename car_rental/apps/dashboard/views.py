from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from apps.accounts.models import CustomUser
from apps.cars.models import Car
from car_rental.apps.bookings.models import Booking


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

@login_required
def owner_bookings(request):
    if request.user.role != "owner":
        return HttpResponseForbidden("You are not authorized.")

    bookings = Booking.objects.filter(
        car__owner=request.user
    ).order_by("-created_at")

    return render(request, "dashboard/owner_bookings.html", {
        "bookings": bookings
    })

@login_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        car__owner=request.user
    )

    if request.user.role != "owner":
        return HttpResponseForbidden("Not authorized.")

    if booking.payment_status != "PAID":
        return HttpResponseForbidden("Payment required before approval.")

    if booking.status != "AWAITING_OWNER_APPROVAL":
        return HttpResponseForbidden("Invalid booking state.")

    booking.status = "APPROVED"
    booking.save()

    return redirect("owner_bookings")
    
@login_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        car__owner=request.user
    )

    if request.user.role != "owner":
        return HttpResponseForbidden("Not authorized.")

    if booking.status not in ["PENDING", "AWAITING_OWNER_APPROVAL"]:
        return HttpResponseForbidden("Cannot reject this booking.")

    booking.status = "REJECTED"
    booking.save()

    return redirect("owner_bookings")
