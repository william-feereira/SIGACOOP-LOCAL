from django.urls import path
from .views import index
app_name="fleet"
urlpatterns=[path("",index,name="index")]
