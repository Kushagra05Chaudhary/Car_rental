from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from .forms import CarForm
from .models import Car

@login_required
@role_required('owner')
def add_car(request):

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)
            car.owner = request.user
            car.status = 'pending'
            car.save()
            return redirect('owner_dashboard')
    else:
        form = CarForm()

    return render(request, 'cars/add_car.html', {'form': form})


def car_list(request):
    cars = Car.objects.filter(status='approved')
    return render(request, 'cars/car_list.html', {'cars': cars})


def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk, status='approved')
    return render(request, 'cars/car_detail.html', {'car': car})
