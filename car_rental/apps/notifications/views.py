from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Notification


@login_required
def notification_list(request):
	notifications = Notification.objects.filter(user=request.user)

	return render(request, 'notifications/list.html', {
		'notifications': notifications
	})
