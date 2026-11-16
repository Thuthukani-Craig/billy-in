import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'billyin.settings')
import django
django.setup()
from django.conf import settings
print(settings.CORS_ALLOWED_ORIGINS)
print(settings.CSRF_TRUSTED_ORIGINS)
