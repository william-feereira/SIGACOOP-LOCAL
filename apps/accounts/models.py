from django.conf import settings
from django.db import models
from apps.core.models import Unit, Department, TimeStampedModel


class UserProfile(TimeStampedModel):
    """Dados do colaborador. O perfil de acesso fica nos Grupos do Django (ver apps.core.access)."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="siga_profile")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, null=True, blank=True, verbose_name="unidade principal")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True, verbose_name="setor")
    entra_oid = models.CharField(max_length=64, blank=True, unique=True, null=True)

    class Meta:
        verbose_name = "perfil do colaborador"
        verbose_name_plural = "perfis dos colaboradores"

    def __str__(self):
        return self.user.get_username()


class AcessoUnidade(TimeStampedModel):
    """Acesso a uma unidade além da principal (ex.: gestor regional que cobre vários PAs)."""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="acessos_unidade")
    unidade = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="acessos")
    concedido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+")

    class Meta:
        verbose_name = "acesso a unidade"
        verbose_name_plural = "acessos a unidades"
        constraints = [models.UniqueConstraint(fields=["usuario", "unidade"], name="acesso_unidade_unico")]

    def __str__(self):
        return f"{self.usuario} → {self.unidade}"
