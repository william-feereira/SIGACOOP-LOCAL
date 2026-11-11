from django.contrib import admin

from .models import AcaoReforma, MembroReforma, Reforma, RegistroAndamento


class MembroInline(admin.TabularInline):
    model = MembroReforma
    extra = 0


@admin.register(Reforma)
class ReformaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "titulo", "unidade", "situacao", "inicio", "fim_previsto")
    list_filter = ("situacao", "unidade")
    search_fields = ("codigo", "titulo")
    readonly_fields = ("codigo", "criado_por")
    inlines = [MembroInline]


@admin.register(AcaoReforma)
class AcaoReformaAdmin(admin.ModelAdmin):
    """Só consulta: mover, bloquear e passar adiante passam pelas regras em servicos.py."""
    list_display = ("titulo", "reforma", "coluna", "responsavel", "fornecedor", "prazo")
    list_filter = ("coluna", "reforma__unidade")

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RegistroAndamento)
class RegistroAndamentoAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "acao", "tipo", "autor")
    list_filter = ("tipo",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
