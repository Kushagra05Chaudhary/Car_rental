from django.db import models
from django.conf import settings

class Car(models.Model):

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'owner'}
    )

    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    seats = models.IntegerField()
    image = models.ImageField(upload_to='car_images/', null=True, blank=True)

    def __str__(self):
        return self.name
