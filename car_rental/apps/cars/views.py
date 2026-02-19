from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from apps.accounts.decorators import role_required
from .forms import OwnerCarForm
from .models import Car
from .services import AdminCarModerationService


# ============ PUBLIC VIEWS ============

def car_list(request):
    """List all approved and available cars"""
    cars = Car.objects.filter(status='approved', is_available=True)
    return render(request, 'cars/car_list.html', {
        'cars': cars
    })


def car_detail(request, pk):
    """View car details"""
    car = get_object_or_404(
        Car,
        pk=pk,
        status='approved'
    )
    return render(request, 'cars/car_detail.html', {
        'car': car
    })


# ============ OWNER VIEWS (Class-Based) ============

class OwnerCarMixin(UserPassesTestMixin, LoginRequiredMixin):
    """Mixin to ensure only owners can access car management"""
    login_url = 'login'
    
    def test_func(self):
        """Check if user is owner"""
        return self.request.user.role == 'owner'
    
    def handle_no_permission(self):
        """Redirect if no permission"""
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


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('admin'), name='dispatch')
class AdminCarListView(TemplateView):
    template_name = 'cars/admin_car_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner_id = self.request.GET.get('owner')
        availability = self.request.GET.get('availability')
        query = self.request.GET.get('q')

        cars = AdminCarModerationService.get_cars(owner_id=owner_id, availability=availability, query=query)
        context['cars'] = cars
        context['owners'] = cars.values('owner__id', 'owner__username').distinct().order_by('owner__username')
        context['filters'] = {
            'owner': owner_id or '',
            'availability': availability or '',
            'q': query or '',
        }
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('admin'), name='dispatch')
class AdminCarAvailabilityToggleView(View):
    def post(self, request, pk, *args, **kwargs):
        car = get_object_or_404(Car, pk=pk)
        AdminCarModerationService.toggle_availability(car)
        messages.success(request, f'{car.name} availability updated.')
        return redirect('admin_car_list')


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('admin'), name='dispatch')
class AdminCarFeatureToggleView(View):
    def post(self, request, pk, *args, **kwargs):
        car = get_object_or_404(Car, pk=pk)
        AdminCarModerationService.toggle_featured(car)
        messages.success(request, f'{car.name} featured status updated.')
        return redirect('admin_car_list')


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('admin'), name='dispatch')
class AdminCarBulkActionView(View):
    def post(self, request, *args, **kwargs):
        car_ids = request.POST.getlist('car_ids')
        action = request.POST.get('action')
        queryset = Car.objects.filter(id__in=car_ids)
        updated = AdminCarModerationService.bulk_update(queryset, action)

        if updated:
            messages.success(request, f'Bulk action applied to {updated} car(s).')
        else:
            messages.warning(request, 'No cars were updated.')
        return redirect('admin_car_list')