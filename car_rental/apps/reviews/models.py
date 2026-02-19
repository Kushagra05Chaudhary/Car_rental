from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.cars.models import Car


class Review(models.Model):
	RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
	car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='reviews')
	rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
	comment = models.TextField(blank=True)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ['-created_at']
		unique_together = ('user', 'car')

	def __str__(self):
		return f"{self.user.username} - {self.car.name} ({self.rating})"
