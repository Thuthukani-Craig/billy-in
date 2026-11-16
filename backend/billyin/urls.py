from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('accounts.urls')),
    path('api/v1/businesses/', include('businesses.urls')),
    path('api/v1/customers/', include('customers.urls')),
    path('api/v1/documents/', include('documents.urls')),
    path('api/v1/payments/', include('payments.urls')),
    path('api/v1/reporting/', include('reporting.urls')),
]
