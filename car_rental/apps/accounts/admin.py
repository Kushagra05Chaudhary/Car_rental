from django.contrib import admin
from .models import CustomUser, OwnerRequest
from django.contrib.auth.admin import UserAdmin

# Register your models here.    

admin.site.register(CustomUser, UserAdmin)

class OwnerRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.status == 'approved':
            user = obj.user
            user.role = 'owner'
            user.save()


admin.site.register(OwnerRequest, OwnerRequestAdmin)