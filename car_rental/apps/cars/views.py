from django.db.models import Avg
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from apps.accounts.decorators import role_required
from apps.reviews.models import Review
from .forms import OwnerCarForm
from .models import Car


# ============ PUBLIC VIEWS ============

def car_list(request):
    """List all approved and available cars with filters"""
    from django.db.models import Q

    search     = request.GET.get('search', '').strip()
    car_type   = request.GET.get('car_type', '')
    location   = request.GET.get('location', '').strip()
    max_price  = request.GET.get('max_price', '')
    min_seats  = request.GET.get('min_seats', '')
    sort       = request.GET.get('sort', 'newest')

    cars = Car.objects.filter(status='approved', is_available=True)

    if search:
        cars = cars.filter(Q(name__icontains=search) | Q(brand__icontains=search))
    if car_type:
        cars = cars.filter(car_type__iexact=car_type)
    if location:
        cars = cars.filter(location__icontains=location)
    if max_price:
        try:
            cars = cars.filter(price_per_day__lte=int(max_price))
        except ValueError:
            pass
    if min_seats:
        try:
            cars = cars.filter(seats__gte=int(min_seats))
        except ValueError:
            pass

    sort_map = {
        'price_asc':  'price_per_day',
        'price_desc': '-price_per_day',
        'newest':     '-created_at',
        'seats':      '-seats',
    }
    cars = cars.order_by(sort_map.get(sort, '-created_at'))

    # Distinct locations and types for dropdowns
    all_locations = Car.objects.filter(status='approved', is_available=True).values_list('location', flat=True).distinct().order_by('location')
    all_types     = Car.objects.filter(status='approved', is_available=True).values_list('car_type', flat=True).distinct().order_by('car_type')
    max_db_price  = Car.objects.filter(status='approved', is_available=True).order_by('-price_per_day').values_list('price_per_day', flat=True).first() or 10000

    return render(request, 'cars/car_list.html', {
        'cars': cars,
        'search':    search,
        'car_type':  car_type,
        'location':  location,
        'max_price': max_price or int(max_db_price),
        'min_seats': min_seats,
        'sort':      sort,
        'all_locations': all_locations,
        'all_types':     all_types,
        'max_db_price':  int(max_db_price),
        'active_filters': any([search, car_type, location, max_price, min_seats]),
    })

def car_detail(request, pk):
    """View car details"""
    car = get_object_or_404(
        Car,
        pk=pk,
        status='approved'
    )
    reviews = Review.objects.filter(car=car).select_related('user').order_by('-created_at')
    rating_average = reviews.aggregate(avg=Avg('rating'))['avg']

    return render(request, 'cars/car_detail.html', {
        'car': car,
        'reviews': reviews,
        'rating_average': rating_average,
        'rating_count': reviews.count(),
    })


# ============ OWNER VIEWS (Class-Based) ============

class OwnerCarMixin(UserPassesTestMixin, LoginRequiredMixin):
    """Mixin to ensure only owners can access car management"""
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


class OwnerCarListView(OwnerCarMixin, ListView):
    """Owner's car list - shows only their cars"""
    model = Car
    template_name = 'cars/owner_car_list.html'
    context_object_name = 'cars'
    paginate_by = 10
    
    def get_queryset(self):
        """Filter cars by current owner"""
        return Car.objects.filter(owner=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cars = self.get_queryset()
        
        # Add statistics
        context['total_cars'] = cars.count()
        context['active_cars'] = cars.filter(is_available=True).count()
        context['pending_cars'] = cars.filter(status='pending').count()
        context['approved_cars'] = cars.filter(status='approved').count()
        
        return context


class OwnerCarCreateView(OwnerCarMixin, CreateView):
    """Add new car for owner"""
    model = Car
    form_class = OwnerCarForm
    template_name = 'cars/owner_add_car.html'
    
    def form_valid(self, form):
        """Set owner to current user"""
        form.instance.owner = self.request.user
        form.instance.status = 'pending'  # Admin approval required
        
        messages.success(
            self.request,
            'Car added successfully! It will be available after admin approval.'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('owner_car_list')


class OwnerCarUpdateView(OwnerCarMixin, UpdateView):
    """Edit car details"""
    model = Car
    form_class = OwnerCarForm
    template_name = 'cars/owner_edit_car.html'
    
    def get_queryset(self):
        """Ensure owner can only edit their cars"""
        return Car.objects.filter(owner=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Car updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('owner_car_list')


class OwnerCarDeleteView(OwnerCarMixin, DeleteView):
    """Delete car"""
    model = Car
    template_name = 'cars/owner_delete_car.html'
    success_url = reverse_lazy('owner_car_list')
    
    def get_queryset(self):
        """Ensure owner can only delete their cars"""
        return Car.objects.filter(owner=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Car deleted successfully!')
        return super().delete(request, *args, **kwargs)


class OwnerCarToggleAvailabilityView(OwnerCarMixin, UpdateView):
    """Toggle car availability"""
    model = Car
    fields = ['is_available']
    template_name = 'cars/owner_car_list.html'
    
    def get_queryset(self):
        """Ensure owner can only toggle their cars"""
        return Car.objects.filter(owner=self.request.user)
    
    def form_valid(self, form):
        car = form.save()
        status = "available" if car.is_available else "unavailable"
        messages.success(self.request, f'Car marked as {status}!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('owner_car_list')
