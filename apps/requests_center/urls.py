from django.urls import path
from . import views
app_name="requests_center"
urlpatterns=[path("",views.request_list,name="list"),path("nova/",views.request_create,name="create"),path("<uuid:pk>/",views.request_detail,name="detail")]
