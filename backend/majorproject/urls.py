"""
URL configuration for majorproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from accounts.views import RegisterView, LoginView, ProfileView, LogoutView, ChangePasswordView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from bills.views import BillViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'bills', BillViewSet, basename='bill')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path("api/register/",RegisterView.as_view()),
    path("api/login/",LoginView.as_view()),
    path("api/logout/",LogoutView.as_view()),
    path("api/change-password/", ChangePasswordView.as_view()),
    path("api/profile/",ProfileView.as_view()),
    path('admin/', admin.site.urls),
    path('api/', include('reports.urls')),  # Reports and financial statements - MUST come before router
    path('api/', include(router.urls)),  # Bills and categories router
]
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns += [
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)