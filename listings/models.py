from django.db import models
from django.utils import timezone


class District(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class PropertyOwner(models.Model):
    phone_number = models.CharField(max_length=20, db_index=True, unique=True)
    full_name = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        # Normalize phone number: remove +, spaces, dashes
        if self.phone_number:
            self.phone_number = self.phone_number.replace('+', '').replace(' ', '').replace('-', '')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name or self.phone_number}"


class Listing(models.Model):
    PROPERTY_TYPE_CHOICES = (
        ('novostroyka', 'Новостройка'),
        ('vtorichka', 'Вторичка'),
    )
    DEAL_TYPE_CHOICES = (
        ('sale', 'Продажа'),
        ('rent', 'Аренда'),
    )
    owner = models.ForeignKey(
        PropertyOwner,
        on_delete=models.CASCADE,
        related_name='listings'
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_listings'
    )
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    deal_type = models.CharField(max_length=10, choices=DEAL_TYPE_CHOICES)
    rooms_count = models.PositiveSmallIntegerField()
    floor = models.PositiveSmallIntegerField()
    total_floors = models.PositiveSmallIntegerField()
    total_area = models.DecimalField(max_digits=8, decimal_places=2)
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name='listings'
    )
    address = models.TextField(blank=True, help_text="To'liq manzil")
    nearby = models.TextField(blank=True, help_text="Yaqinidagi obyektlar")
    amenities = models.TextField(blank=True, help_text="Qo'shimcha sharoitlar (lift, internet, etc.)")
    price = models.DecimalField(max_digits=14, decimal_places=2)
    price_per_sqm = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    registered_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.total_area:
            self.price_per_sqm = round(self.price / self.total_area, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_property_type_display()} - {self.district.name} - {self.rooms_count} xona"

    class Meta:
        ordering = ['-registered_at']

def listing_image_path(instance, filename):
    return f"listings/{instance.listing_id}/{filename}"


class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to=listing_image_path)
    order = models.PositiveSmallIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.listing}"

    class Meta:
        ordering = ['order', 'id']
