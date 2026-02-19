from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, View
from django.urls import reverse_lazy
from django.http import Http404
from django.utils.decorators import method_decorator
from apps.accounts.decorators import role_required
from .models import Booking
from .services import OwnerBookingService, UserBookingService, AdminBookingService
from apps.payments.services import PaymentAdminService


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


@method_decorator(role_required('admin'), name='dispatch')
class AdminBookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/admin_booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 20
    login_url = 'login'

    def get_queryset(self):
        return AdminBookingService.get_bookings(
            status=self.request.GET.get('status') or None,
            start_date=self.request.GET.get('start_date') or None,
            end_date=self.request.GET.get('end_date') or None,
            query=self.request.GET.get('q') or None,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filters'] = {
            'status': self.request.GET.get('status', ''),
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
            'q': self.request.GET.get('q', ''),
        }
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('admin'), name='dispatch')
class AdminCancelBookingView(View):
    def post(self, request, pk, *args, **kwargs):
        booking = get_object_or_404(Booking, pk=pk)
        try:
            AdminBookingService.cancel_booking(booking)
            messages.success(request, 'Booking has been cancelled.')
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect('admin_booking_list')


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('admin'), name='dispatch')
class AdminRefundBookingView(View):
    def post(self, request, pk, *args, **kwargs):
        booking = get_object_or_404(Booking.objects.select_related('payment'), pk=pk)

        if not hasattr(booking, 'payment'):
            messages.error(request, 'No payment record found for this booking.')
            return redirect('admin_booking_list')

        if not AdminBookingService.can_refund(booking):
            messages.error(request, 'This booking is not eligible for refund.')
            return redirect('admin_booking_list')

        try:
            PaymentAdminService.refund_payment(booking.payment)
            messages.success(request, 'Payment refunded successfully.')
        except ValueError as exc:
            messages.error(request, str(exc))

        return redirect('admin_booking_list')

