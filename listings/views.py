from rest_framework import viewsets, status, filters, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions, parsers
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import District, PropertyOwner, Listing, ListingImage
from .serializers import (
    DistrictSerializer,
    PropertyOwnerSerializer,
    ListingSerializer,
    ListingCreateSerializer,
    ListingUpdateSerializer,
    ListingImageUploadSerializer,
)
from .pagination import StandardResultsPagination


class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and viewing districts.
    Provides read-only access to all available districts.
    """
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    pagination_class = None


class ListingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing property listings.
    Provides full CRUD operations with filtering, search, and image upload.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['district', 'property_type', 'deal_type', 'rooms_count']
    search_fields = ['owner__phone_number', 'owner__full_name']
    pagination_class = StandardResultsPagination
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        return Listing.objects.select_related('district', 'owner', 'created_by').prefetch_related('images')

    def get_serializer_class(self):
        if self.action == 'create':
            return ListingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ListingUpdateSerializer
        return ListingSerializer

    @extend_schema(
        operation_id='upload_listing_images',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'image': {'type': 'string', 'format': 'binary'},
                    'images': {'type': 'array', 'items': {'type': 'string', 'format': 'binary'}}
                }
            }
        },
        responses={201: {'type': 'object', 'properties': {'detail': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'], parser_classes=[parsers.MultiPartParser, parsers.FormParser])
    def images(self, request, pk=None):
        """
        Upload images to a listing.
        Maximum 15 images per listing.
        """
        listing = self.get_object()
        serializer = ListingImageUploadSerializer(
            data=request.data,
            context={'listing': listing}
        )
        serializer.is_valid(raise_exception=True)
        
        images = []
        for order, image_file in enumerate(serializer.validated_data['images'], start=listing.images.count()):
            image = ListingImage.objects.create(
                listing=listing,
                image=image_file,
                order=order
            )
            images.append(image)
        
        return Response(
            {'detail': f'{len(images)} ta rasm muvaffaqiyatli qo\'shildi'},
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        operation_id='delete_listing_image',
        parameters=[
            OpenApiParameter(
                name='image_id',
                type=OpenApiTypes.INT,
                location='path',
                description='ID of the image to delete'
            )
        ],
        responses={200: None, 404: None}
    )
    @action(
        detail=True, 
        methods=['delete'], 
        url_path='images/(?P<image_id>[^/.]+)',
    )
    def delete_image(self, request, pk=None, image_id=None):
        """
        Delete a specific image from a listing.
        """
        listing = self.get_object()
        try:
            image = listing.images.get(id=image_id)
            image.delete()
            return Response({'detail': 'Rasm muvaffaqiyatli o\'chirildi'})
        except ListingImage.DoesNotExist:
            return Response(
                {'detail': 'Rasm topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )


class ListingImageViewSet(viewsets.ViewSet):
    """
    API endpoint for managing listing images globally.
    Allows deleting images by ID without specifying listing.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id='delete_image_by_id',
        parameters=[
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.INT,
                location='path',
                description='ID of the image to delete'
            )
        ],
        responses={200: None, 404: None}
    )
    def destroy(self, request, pk=None):
        """
        Delete an image by ID.
        Can delete any image regardless of which listing it belongs to.
        """
        try:
            image = ListingImage.objects.get(id=pk)
            image.delete()
            return Response({'detail': 'Rasm muvaffaqiyatli o\'chirildi'})
        except ListingImage.DoesNotExist:
            return Response(
                {'detail': 'Rasm topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )


class SearchByPhoneView(generics.GenericAPIView):
    """
    API endpoint for searching listings by property owner phone number.
    Returns all listings associated with the given phone number.
    Normalizes phone number format for better matching.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ListingSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='phone',
                type=OpenApiTypes.STR,
                location='query',
                description='Phone number to search for (e.g., +998543253453 or 998543253453)'
            )
        ]
    )
    def get(self, request):
        phone = request.query_params.get('phone')
        if not phone:
            return Response(
                {'detail': 'Telefon raqami kiritilmadi'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Normalize input phone number: remove +, spaces, dashes, parentheses
        normalized_phone = phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Get all owners and filter manually to handle different formats
        all_owners = PropertyOwner.objects.all()
        matching_owners = []
        
        for owner in all_owners:
            # Normalize owner phone number
            owner_phone_normalized = owner.phone_number.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if normalized_phone in owner_phone_normalized or owner_phone_normalized in normalized_phone:
                matching_owners.append(owner)
        
        if not matching_owners:
            return Response([], status=status.HTTP_200_OK)
        
        listings = Listing.objects.filter(
            owner__in=matching_owners
        ).select_related('district', 'owner')
        
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)


class DashboardStatsView(generics.GenericAPIView):
    """
    API endpoint for dashboard statistics.
    Returns aggregated statistics about listings.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        listings = Listing.objects.all()
        
        stats = {
            'total_listings': listings.count(),
            'for_sale_count': listings.filter(deal_type='sale').count(),
            'for_rent_count': listings.filter(deal_type='rent').count(),
            'new_buildings_count': listings.filter(property_type='novostroyka').count(),
        }
        
        return Response(stats)
