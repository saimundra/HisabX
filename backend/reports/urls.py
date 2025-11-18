from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet

router = DefaultRouter()
router.register(r'audit_reports', ReportViewSet, basename='audit_report')

urlpatterns = [
    path('reports/', include(router.urls)),
]