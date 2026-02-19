from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, View
from django.urls import reverse_lazy
from django.http import Http404
from .models import Booking
from .services import OwnerBookingService, UserBookingService


# ============ OWNER VIEWS ============

class OwnerBookingMixin(UserPassesTestMixin, LoginRequiredMixin):
    """Mixin to ensure only owners can access booking management"""
    login_url = 'login'
    
    def test_func(self):
        """Check if user is owner"""
        return self.request.user.role == 'owner'
    
    def handle_no_permission(self):
        """Redirect if no permission"""
        messages.error(self.request, 'You must be an owner to access this page.')
        return redirect('car_list')


class OwnerBookingListView(OwnerBookingMixin, ListView):
    """Owner's booking list - shows bookings for their cars"""
    model = Booking
    template_name = 'bookings/owner_booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 15
    
    def get_queryset(self):
        """Get bookings for owner's cars"""
        return OwnerBookingService.get_owner_bookings(self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add statistics
        pending = OwnerBookingService.get_pending_bookings(self.request.user)
        confirmed = OwnerBookingService.get_confirmed_bookings(self.request.user)
        completed = OwnerBookingService.get_completed_bookings(self.request.user)
        
        context['pending_count'] = pending.count()
        context['confirmed_count'] = confirmed.count()
        context['completed_count'] = completed.count()
        context['total_bookings'] = self.get_queryset().count()
        
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

class UserBookingListView(LoginRequiredMixin, ListView):
    """User's booking list"""
    model = Booking
    template_name = 'bookings/user_booking_list.html'
    context_object_name = 'bookings'
    login_url = 'login'
    paginate_by = 15
    
    def get_queryset(self):
        """Get bookings for current user"""
        return UserBookingService.get_user_bookings(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_bookings = UserBookingService.get_user_bookings(self.request.user)
        
        context['active_count'] = UserBookingService.get_user_active_bookings(
            self.request.user
        ).count()
        context['total_bookings'] = user_bookings.count()
        
        return context


class UserBookingDetailView(LoginRequiredMixin, DetailView):
    """View booking details for user"""
    model = Booking
    template_name = 'bookings/user_booking_detail.html'
    context_object_name = 'booking'
    login_url = 'login'
    
    def get_queryset(self):
        """Ensure user can only view their bookings"""
        return Booking.objects.filter(user=self.request.user)

