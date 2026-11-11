from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.reformas.models import AcaoReforma, Reforma


class CarregarDemoTests(TestCase):
    def test_recusa_fora_do_modo_local(self):
        with self.assertRaises(CommandError):
            call_command("carregar_demo", senha="demo-local-senha-longa")

    @override_settings(SIGA_PERMITIR_DEMO=True)
    def test_recusa_senha_fraca(self):
        with self.assertRaises(CommandError):
            call_command("carregar_demo", senha="123")

    @override_settings(SIGA_PERMITIR_DEMO=True)
    def test_cria_cenario_e_nao_duplica(self):
        call_command("carregar_demo", senha="demo-local-senha-longa")
        call_command("carregar_demo", senha="demo-local-senha-longa")
        self.assertEqual(Reforma.objects.count(), 1)
        self.assertEqual(AcaoReforma.objects.filter(coluna="BLOQUEADA").count(), 1)
