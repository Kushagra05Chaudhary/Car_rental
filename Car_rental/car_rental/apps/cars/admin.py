from django.contrib import admin
from .models import Car

class CarAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'created_at')
    list_filter = ('status',)
    actions = ['approve_cars', 'reject_cars']

    def approve_cars(self, request, queryset):
        queryset.update(status='approved')
    approve_cars.short_description = "Approve selected cars"

    def reject_cars(self, request, queryset):
        queryset.update(status='rejected')
    reject_cars.short_description = "Reject selected cars"

admin.site.register(Car, CarAdmin)
