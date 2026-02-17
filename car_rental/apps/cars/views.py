from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from .forms import CarForm

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
