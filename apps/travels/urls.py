from django.urls import path
from .views import index
app_name="travels"
urlpatterns=[path("",index,name="index")]
