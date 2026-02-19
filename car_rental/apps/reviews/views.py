from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.bookings.models import Booking
from .forms import ReviewForm
from .models import Review


@login_required
def create_review(request, booking_id):
	booking = get_object_or_404(Booking, id=booking_id, user=request.user)

	if booking.status != 'completed':
		messages.error(request, 'You can only review completed bookings.')
		return redirect('booking_list')

	if hasattr(booking, 'review'):
		messages.info(request, 'You have already reviewed this booking.')
		return redirect('booking_list')

	if request.method == 'POST':
		form = ReviewForm(request.POST)
		if form.is_valid():
			review = form.save(commit=False)
			review.booking = booking
			review.car = booking.car
			review.user = request.user
			review.save()
			messages.success(request, 'Review submitted successfully.')
			return redirect('booking_list')
	else:
		form = ReviewForm()

	return render(request, 'reviews/create_review.html', {
		'form': form,
		'booking': booking,
	})
