from django.urls import path

from .views import DocumentViewSet, DocumentDesignProfileViewSet

urlpatterns = [
    path('design-profiles/', DocumentDesignProfileViewSet.as_view({'get': 'list', 'post': 'create'}), name='document-design-profile-list'),
    path('design-profiles/<int:pk>/', DocumentDesignProfileViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='document-design-profile-detail'),
    path('', DocumentViewSet.as_view({'get': 'list', 'post': 'create'}), name='document-list'),
    path('<int:pk>/pdf/', DocumentViewSet.as_view({'get': 'pdf'}), name='document-pdf'),
    path('<int:pk>/', DocumentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='document-detail'),
]
