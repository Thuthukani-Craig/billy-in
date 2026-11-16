from django.urls import path

from .views import CurrentUserView, FounderRegistrationView, LoginView, LogoutView, TenantViewSet

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/', CurrentUserView.as_view(), name='current-user'),
    path('auth/register-founder/', FounderRegistrationView.as_view(), name='register-founder'),
    path('tenants/', TenantViewSet.as_view({'get': 'list', 'post': 'create'}), name='tenant-list'),
    path('tenants/<int:pk>/', TenantViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='tenant-detail'),
]
