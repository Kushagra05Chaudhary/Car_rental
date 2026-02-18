from django.shortcuts import render
from apps.cars.models import Car

# Create your views here.

def home(request):
    cars = Car.objects.filter(status="approved")

    location = request.GET.get("location")
    if location:
        cars = cars.filter(location__icontains=location)

    featured_cars = cars[:6]

    return render(request, "core/home.html", {
        "featured_cars": featured_cars
    })
