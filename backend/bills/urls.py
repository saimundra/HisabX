from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BillViewSet, CategoryViewSet

app_name = 'bills'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'bills', BillViewSet, basename='bill')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]
