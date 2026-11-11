from django.urls import path
from django.views.generic import TemplateView

from .views import home

app_name = "core"
urlpatterns = [
    path("privacidade/", TemplateView.as_view(template_name="core/privacy.html"), name="privacy"),
    path("termos/", TemplateView.as_view(template_name="core/terms.html"), name="terms"),
    path("inicio/", home, name="home"),
]
