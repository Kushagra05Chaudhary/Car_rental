from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from .models import Notification


@login_required
def notification_list(request):
	if request.user.role == 'admin':
		messages.error(request, 'Admins can only access admin features.')
		return redirect('admin_dashboard')

	notifications = Notification.objects.filter(user=request.user)

	return render(request, 'notifications/list.html', {
		'notifications': notifications
	})
