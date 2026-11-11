from django.contrib import admin
from .models import AcessoUnidade, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "unit", "department")
    list_filter = ("unit",)
    search_fields = ("user__username", "user__first_name", "user__last_name")


@admin.register(AcessoUnidade)
class AcessoUnidadeAdmin(admin.ModelAdmin):
    list_display = ("usuario", "unidade", "concedido_por", "created_at")
    list_filter = ("unidade",)
    autocomplete_fields = ()

    def save_model(self, request, obj, form, change):
        if not obj.concedido_por_id:
            obj.concedido_por = request.user
        super().save_model(request, obj, form, change)
