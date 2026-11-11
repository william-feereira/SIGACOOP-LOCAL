from django.contrib import admin
from .models import AdministrativeRequest,RequestEvent
admin.site.register([AdministrativeRequest,RequestEvent])
