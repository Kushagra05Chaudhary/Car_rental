from django.db import models
from django.conf import settings
from django.utils import timezone

from apps.bookings.models import Booking
from apps.cars.models import Car


class Review(models.Model):
	"""Review for a completed booking."""

	booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
	car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='reviews')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')

	rating = models.PositiveSmallIntegerField()
	comment = models.TextField(blank=True)

	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"Review - {self.car.name} - {self.rating}"
