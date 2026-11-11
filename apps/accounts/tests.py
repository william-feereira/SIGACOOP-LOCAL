from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django_otp.oath import totp
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.core.access import ADMINISTRADOR, GESTOR, PERFIS

User = get_user_model()


def codigo_atual(dispositivo):
    return f"{totp(dispositivo.bin_key, dispositivo.step, dispositivo.t0, dispositivo.digits, dispositivo.drift):06d}"


class PerfisTests(TestCase):
    def test_perfis_criados_no_migrate(self):
        self.assertEqual(set(Group.objects.filter(name__in=PERFIS).values_list("name", flat=True)), set(PERFIS))

    def test_diretoria_so_tem_permissoes_de_leitura(self):
        perms = Group.objects.get(name="Diretoria").permissions.values_list("codename", flat=True)
        self.assertTrue(perms)
        self.assertTrue(all(p.startswith("view_") for p in perms))

    def test_ninguem_altera_auditoria(self):
        for grupo in Group.objects.all():
            self.assertFalse(grupo.permissions.filter(content_type__app_label="audit").exclude(codename__startswith="view_").exists())


class MfaTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin", password="senha-de-teste-longa")
        self.admin.groups.add(Group.objects.get(name=ADMINISTRADOR))

    def test_admin_sem_mfa_e_levado_para_configurar(self):
        self.client.force_login(self.admin)
        r = self.client.get("/solicitacoes/")
        self.assertRedirects(r, "/contas/verificacao/configurar/?next=/solicitacoes/", fetch_redirect_response=False)

    def test_configurar_e_verificar_libera_navegacao(self):
        self.client.force_login(self.admin)
        r = self.client.get("/contas/verificacao/configurar/")
        self.assertContains(r, "<svg")
        dispositivo = TOTPDevice.objects.get(user=self.admin)
        self.assertFalse(dispositivo.confirmed)
        r = self.client.post("/contas/verificacao/configurar/", {"codigo": "000000"})
        self.assertContains(r, "Código incorreto")
        dispositivo.refresh_from_db()
        dispositivo.throttling_failure_count = 0
        dispositivo.throttling_failure_timestamp = None
        dispositivo.save()
        codigo = codigo_atual(dispositivo)
        r = self.client.post("/contas/verificacao/configurar/?next=/solicitacoes/", {"codigo": f"{codigo[:3]} {codigo[3:]}"})
        self.assertRedirects(r, "/solicitacoes/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/solicitacoes/").status_code, 200)

    def test_nova_sessao_pede_codigo(self):
        TOTPDevice.objects.create(user=self.admin, name="app", confirmed=True)
        self.client.force_login(self.admin)
        r = self.client.get("/")
        self.assertRedirects(r, "/contas/verificacao/?next=/", fetch_redirect_response=False)

    def test_next_externo_e_ignorado(self):
        dispositivo = TOTPDevice.objects.create(user=self.admin, name="app", confirmed=True)
        self.client.force_login(self.admin)
        r = self.client.post("/contas/verificacao/?next=https://malicioso.example/", {"codigo": codigo_atual(dispositivo)})
        self.assertRedirects(r, "/", fetch_redirect_response=False)

    def test_gestor_nao_e_obrigado(self):
        gestor = User.objects.create_user("gestor", password="senha-de-teste-longa")
        gestor.groups.add(Group.objects.get(name=GESTOR))
        self.client.force_login(gestor)
        self.assertEqual(self.client.get("/inicio/").status_code, 200)


class LoginTests(TestCase):
    def setUp(self):
        User.objects.create_user("maria", password="senha-de-teste-longa")

    def test_login_ok(self):
        r = self.client.post("/contas/entrar/", {"username": "maria", "password": "senha-de-teste-longa"})
        self.assertEqual(r.status_code, 302)

    @override_settings(AXES_FAILURE_LIMIT=3)
    def test_bloqueio_apos_tentativas_erradas(self):
        for _ in range(3):
            self.client.post("/contas/entrar/", {"username": "maria", "password": "errada"})
        r = self.client.post("/contas/entrar/", {"username": "maria", "password": "senha-de-teste-longa"})
        self.assertEqual(r.status_code, 429)
        self.assertContains(r, "bloqueado", status_code=429)
