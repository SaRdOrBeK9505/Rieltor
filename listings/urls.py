from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DistrictViewSet,
    ListingViewSet,
    ListingImageViewSet,
    SearchByPhoneView,
    DashboardStatsView,
)

router = DefaultRouter()
router.register(r'districts', DistrictViewSet, basename='district')
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'images', ListingImageViewSet, basename='image')

urlpatterns = [
    path('', include(router.urls)),
    path('search/by-phone/', SearchByPhoneView.as_view(), name='search-by-phone'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
