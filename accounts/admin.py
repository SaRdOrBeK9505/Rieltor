from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'phone_number', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number')}),
    )
    
    def get_model_perms(self, request, obj=None):
        return {
            'add': True,
            'change': True,
            'delete': True,
            'view': True,
        }
