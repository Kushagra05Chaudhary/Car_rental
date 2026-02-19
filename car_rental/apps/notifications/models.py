from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
	"""Simple in-app notification."""

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
	title = models.CharField(max_length=200)
	message = models.TextField()
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"Notification - {self.user.username} - {self.title}"
