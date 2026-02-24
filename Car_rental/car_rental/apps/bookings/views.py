from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from apps.cars.models import Car
from .models import Booking, BookingHold
from .services import OwnerBookingService, UserBookingService


# ============ OWNER VIEWS ============

class OwnerBookingMixin(UserPassesTestMixin, LoginRequiredMixin):
    """Mixin to ensure only owners can access booking management"""
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


# ============ USER VIEWS ============

class UserBookingMixin(UserPassesTestMixin, LoginRequiredMixin):
    """Mixin to ensure only users can access their bookings"""
    login_url = 'login'
    
    def test_func(self):
        """Check if user is a regular user and not admin, superuser, or owner"""
        if self.request.user.is_superuser or self.request.user.role == 'admin':
            return False
        return self.request.user.role == 'user'
    
    def handle_no_permission(self):
        """Redirect if no permission"""
        if self.request.user.is_superuser or self.request.user.role == 'admin':
            messages.error(self.request, 'Admins can only access admin features.')
            return redirect('admin_dashboard')
        messages.error(self.request, 'You must be a regular user to access this page.')
        return redirect('car_list')


class OwnerBookingListView(OwnerBookingMixin, ListView):
    """Owner's booking list - shows bookings for their cars"""
    model = Booking
    template_name = 'bookings/owner_booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 15
    
    def get_queryset(self):
        """Get bookings for owner's cars"""
        queryset = OwnerBookingService.get_owner_bookings(self.request.user).order_by('-created_at')
        
        # Filter by status if provided
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Transitions already ran in get_queryset — reuse a fresh queryset
        # without triggering auto-transition again.
        all_bookings = Booking.objects.filter(car__owner=self.request.user)
        context['pending_count']   = all_bookings.filter(status='pending').count()
        context['confirmed_count'] = all_bookings.filter(status='confirmed').count()
        context['completed_count'] = all_bookings.filter(status='completed').count()
        context['total_bookings']  = all_bookings.count()

        return context


class OwnerBookingDetailView(OwnerBookingMixin, DetailView):
    """View booking details"""
    model = Booking
    template_name = 'bookings/owner_booking_detail.html'
    context_object_name = 'booking'
    
    def get_object(self, queryset=None):
        """Ensure owner can only view bookings of their cars"""
        booking_id = self.kwargs.get('pk')
        booking = OwnerBookingService.get_booking_details(booking_id, self.request.user)
        
        if not booking:
            raise Http404("Booking not found")
        
        return booking


class OwnerAcceptBookingView(OwnerBookingMixin, View):
    """Accept a pending booking"""
    
    def post(self, request, pk, *args, **kwargs):
        booking = get_object_or_404(Booking, id=pk)
        
        # Verify owner
        if booking.car.owner != request.user:
            messages.error(request, 'You can only accept bookings for your cars.')
            return redirect('owner_booking_list')
        
        try:
            OwnerBookingService.accept_booking(booking)
            messages.success(request, 'Booking accepted successfully!')
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('owner_booking_detail', pk=booking.id)


class OwnerRejectBookingView(OwnerBookingMixin, View):
    """Reject a pending booking"""
    
    def post(self, request, pk, *args, **kwargs):
        booking = get_object_or_404(Booking, id=pk)
        
        # Verify owner
        if booking.car.owner != request.user:
            messages.error(request, 'You can only reject bookings for your cars.')
            return redirect('owner_booking_list')
        
        try:
            OwnerBookingService.reject_booking(booking)
            messages.success(request, 'Booking rejected successfully!')
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('owner_booking_list')


# ============ USER VIEWS ============

class UserBookingListView(UserBookingMixin, ListView):
    """User's booking list"""
    model = Booking
    template_name = 'bookings/user_booking.html'
    context_object_name = 'bookings'
    paginate_by = 15
    
    def get_queryset(self):
        """Get bookings for current user"""
        return UserBookingService.get_user_bookings(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # object_list is the full queryset (transitions already ran in get_queryset)
        context['active_count']  = UserBookingService.get_user_active_bookings(
            self.request.user
        ).count()
        context['total_bookings'] = self.object_list.count()
        return context


class UserBookingDetailView(LoginRequiredMixin, DetailView):
    """View booking details for user — only the booking owner may access it."""
    model = Booking
    template_name = 'bookings/user_booking_detail.html'
    context_object_name = 'booking'
    login_url = 'login'

    def get_object(self, queryset=None):
        """Return the booking only if it belongs to the logged-in user."""
        booking = get_object_or_404(Booking, pk=self.kwargs['pk'])
        if booking.user != self.request.user:
            raise Http404("Booking not found.")
        return booking

    def get(self, request, *args, **kwargs):
        """Block admins and superusers from user views."""
        if request.user.is_superuser or request.user.role == 'admin':
            messages.error(request, 'Admins can only access admin features.')
            return redirect('admin_dashboard')
        return super().get(request, *args, **kwargs)


@login_required
def create_booking(request, car_id):
    if request.user.is_superuser or request.user.role == 'admin':
        messages.error(request, 'Admins can only access admin features.')
        return redirect('admin_dashboard')

    car = get_object_or_404(Car, id=car_id, status='approved')

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            messages.error(request, 'Please provide valid dates.')
            return render(request, 'bookings/create_booking.html', {'car': car})

        if end < start:
            messages.error(request, 'End date must be same as or after start date.')
            return render(request, 'bookings/create_booking.html', {'car': car})

        if UserBookingService.has_conflicts(car, start, end, exclude_user=request.user):
            messages.error(request, 'This car is already reserved for the selected dates.')
            return render(request, 'bookings/create_booking.html', {'car': car})

        hold_minutes = getattr(settings, 'BOOKING_HOLD_MINUTES', 10)
        hold = UserBookingService.create_hold(request.user, car, start, end, hold_minutes=hold_minutes)

        # Do NOT create a Booking here — the booking is only created after
        # the user actually completes payment (in initiate_payment / payment_success).
        # Until then only the Hold exists, so abandoned checkouts leave no DB clutter.
        return redirect('razorpay_checkout_hold', hold_id=hold.id)

    return render(request, 'bookings/create_booking.html', {'car': car})


def car_booked_dates(request, car_id):
    """Return booked/held dates for a car as JSON for the availability calendar."""
    car = get_object_or_404(Car, id=car_id)

    booked_dates = set()

    # Collect dates from blocking bookings:
    # confirmed, ongoing, or pending-with-payment-received
    bookings = Booking.objects.filter(
        car=car,
    ).filter(
        Q(status__in=['confirmed', 'ongoing']) |
        Q(status='pending', payment_status='paid')
    )
    for booking in bookings:
        current = booking.start_date
        while current <= booking.end_date:
            booked_dates.add(current.isoformat())
            current += timedelta(days=1)

    # Collect dates from active holds (not expired)
    holds = BookingHold.objects.filter(
        car=car,
        expires_at__gt=timezone.now(),
    )
    for hold in holds:
        current = hold.start_date
        while current <= hold.end_date:
            booked_dates.add(current.isoformat())
            current += timedelta(days=1)

    return JsonResponse({'booked_dates': sorted(booked_dates)})
