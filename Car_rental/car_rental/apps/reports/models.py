from django.db import models
from django.conf import settings
from django.utils import timezone


class OwnerReport(models.Model):
    """Track owner earnings and revenue reports"""
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_bookings = models.IntegerField(default=0)
    completed_bookings = models.IntegerField(default=0)
    pending_bookings = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Report - {self.owner.username} ({self.generated_at.date()})"
