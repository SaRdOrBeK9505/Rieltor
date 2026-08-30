from rest_framework import serializers
from typing import Optional
from .models import District, PropertyOwner, Listing, ListingImage


class DistrictSerializer(serializers.ModelSerializer):
    """
    Serializer for District model.
    Used for listing all available districts.
    """
    class Meta:
        model = District
        fields = ['id', 'name']


class PropertyOwnerSerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyOwner model.
    Represents property owners with their contact information.
    """
    class Meta:
        model = PropertyOwner
        fields = ['id', 'phone_number', 'full_name']


class ListingImageSerializer(serializers.ModelSerializer):
    """
    Serializer for ListingImage model.
    Includes image URL for easy access to the image file.
    """
    image_url = serializers.SerializerMethodField(
        help_text="Full URL of the image"
    )

    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'image_url', 'order', 'uploaded_at']
        read_only_fields = ['uploaded_at']

    def get_image_url(self, obj: ListingImage) -> Optional[str]:
        if obj.image:
            return obj.image.url
        return None


class ListingSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Listing model.
    Includes all related information for display purposes.
    """
    owner_phone = serializers.CharField(
        source='owner.phone_number',
        read_only=True,
        help_text="Property owner's phone number"
    )
    owner_name = serializers.CharField(
        source='owner.full_name',
        read_only=True,
        help_text="Property owner's full name"
    )
    district_name = serializers.CharField(
        source='district.name',
        read_only=True,
        help_text="District name"
    )
    images = ListingImageSerializer(
        many=True,
        read_only=True,
        help_text="List of listing images"
    )
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True,
        help_text="Username of the user who created this listing"
    )

    class Meta:
        model = Listing
        fields = [
            'id', 'property_type', 'deal_type', 'rooms_count', 'floor',
            'total_floors', 'total_area', 'district', 'district_name',
            'price', 'price_per_sqm', 'registered_at', 'owner', 'owner_phone',
            'owner_name', 'images', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['price_per_sqm', 'created_at', 'updated_at']
        depth = 1


class ListingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new listings.
    Accepts owner_phone and automatically creates/retrieves PropertyOwner.
    Returns the created listing with id.
    """
    owner_phone = serializers.CharField(
        write_only=True,
        help_text="Property owner's phone number (creates owner if not exists)"
    )

    class Meta:
        model = Listing
        fields = [
            'id', 'property_type', 'deal_type', 'rooms_count', 'floor',
            'total_floors', 'total_area', 'district', 'price',
            'registered_at', 'owner_phone'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        owner_phone = validated_data.pop('owner_phone')
        
        owner, created = PropertyOwner.objects.get_or_create(
            phone_number=owner_phone,
            defaults={'full_name': ''}
        )
        
        validated_data['owner'] = owner
        validated_data['created_by'] = self.context['request'].user
        
        return super().create(validated_data)


class ListingUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing listings.
    Allows modification of all listing fields.
    Returns the updated listing with id.
    """
    class Meta:
        model = Listing
        fields = [
            'id', 'property_type', 'deal_type', 'rooms_count', 'floor',
            'total_floors', 'total_area', 'district', 'price',
            'registered_at', 'owner'
        ]
        read_only_fields = ['id']


class ListingImageUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading images to a listing.
    Maximum 15 images per listing.
    """
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        help_text="List of image files to upload (max 15)"
    )
    image = serializers.ImageField(
        required=False,
        help_text="Single image file to upload"
    )

    def validate(self, data):
        # Handle both single image and multiple images
        if 'image' in data:
            data['images'] = [data['image']]
            del data['image']
        
        if 'images' not in data or not data['images']:
            raise serializers.ValidationError("Hech qanday rasm yuborilmadi")
        
        listing = self.context['listing']
        existing_count = listing.images.count()
        if existing_count + len(data['images']) > 15:
            raise serializers.ValidationError(
                f"Maksimal 15 ta rasm. Hozir {existing_count} ta bor, {len(data['images'])} ta qo'shib bo'lmaydi."
            )
        
        return data
