from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from PIL import Image as PilImage
import io
import os

class Car(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'owner'}
    )

    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    car_type = models.CharField(max_length=50, default="Sedan")
    location = models.CharField(max_length=100)

    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    seats = models.IntegerField()
    image = models.ImageField(upload_to='car_images/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='car_thumbnails/', null=True, blank=True)

    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate a 400x300 JPEG thumbnail when image changes."""
        # Detect if image has changed
        generate_thumb = False
        if self.pk:
            try:
                old = Car.objects.get(pk=self.pk)
                if old.image != self.image:
                    generate_thumb = True
            except Car.DoesNotExist:
                generate_thumb = bool(self.image)
        else:
            generate_thumb = bool(self.image)

        super().save(*args, **kwargs)

        if generate_thumb and self.image:
            try:
                img = PilImage.open(self.image.path)
                img = img.convert('RGB')
                img.thumbnail((400, 300), PilImage.LANCZOS)

                thumb_io = io.BytesIO()
                img.save(thumb_io, format='JPEG', quality=85)
                thumb_io.seek(0)

                base_name = os.path.splitext(os.path.basename(self.image.name))[0]
                thumb_name = f"{base_name}_thumb.jpg"

                self.thumbnail.save(thumb_name, ContentFile(thumb_io.read()), save=False)
                # Save only the thumbnail field to avoid recursion
                Car.objects.filter(pk=self.pk).update(thumbnail=self.thumbnail)
            except Exception:
                pass  # Silently skip if thumbnail generation fails

