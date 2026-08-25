from django.contrib import admin
from .models import District, PropertyOwner, Listing, ListingImage


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0
    fields = ['image', 'order']
    readonly_fields = ['uploaded_at']


@admin.register(PropertyOwner)
class PropertyOwnerAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'full_name']
    search_fields = ['phone_number', 'full_name']
    ordering = ['phone_number']


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['id', 'property_type', 'deal_type', 'district', 'rooms_count', 'price', 'registered_at', 'created_by']
    list_filter = ['property_type', 'deal_type', 'district', 'rooms_count', 'registered_at']
    search_fields = ['owner__phone_number', 'owner__full_name', 'district__name']
    ordering = ['-registered_at']
    inlines = [ListingImageInline]
    readonly_fields = ['price_per_sqm', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('property_type', 'deal_type', 'district')
        }),
        ('Property Details', {
            'fields': ('rooms_count', 'floor', 'total_floors', 'total_area')
        }),
        ('Owner', {
            'fields': ('owner',)
        }),
        ('Pricing', {
            'fields': ('price', 'price_per_sqm')
        }),
        ('Dates', {
            'fields': ('registered_at', 'created_at', 'updated_at')
        }),
        ('Meta', {
            'fields': ('created_by',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_model_perms(self, request, obj=None):
        return {
            'add': True,
            'change': True,
            'delete': True,
            'view': True,
        }


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ['listing', 'order', 'uploaded_at']
    list_filter = ['uploaded_at']
    ordering = ['listing', 'order', 'id']
    readonly_fields = ['uploaded_at']
