from django.shortcuts import render, get_object_or_404, redirect
from .models import Booking
from apps.cars.models import Car
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def create_booking(request, car_id):
    car = get_object_or_404(Car, id=car_id, is_status='approved')

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        days = (end - start).days
        total_price = days * car.price_per_day

        Booking.objects.create(
            user=request.user,
            car=car,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price
        )

        return redirect('user_bookings')

    return render(request, 'bookings/create_booking.html', {'car': car})

@login_required
def user_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'bookings/user_bookings.html', {
        'bookings': bookings
    })

# Call full_clean() before saving booking to trigger model validation
@login_required
def create_booking(request, car_id):
    car = get_object_or_404(Car, id=car_id, status='approved')

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        days = (end - start).days
        total_price = days * car.price_per_day

        booking = Booking(
            user=request.user,
            car=car,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price
        )

        try:
            booking.full_clean()  # Trigger model validation
            booking.save()
            return redirect('user_bookings')
        except ValidationError as e:
            return render(request, 'bookings/create_booking.html', {
                'car': car,
                'errors': e.message_dict
            })

    return render(request, 'bookings/create_booking.html', {'car': car})