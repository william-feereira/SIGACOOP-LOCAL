"""Defesa no banco: o diário de andamento não aceita UPDATE nem DELETE, nem por fora do Django."""
from django.db import migrations

CRIAR = """
CREATE OR REPLACE FUNCTION reformas_diario_imutavel() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'Registros de andamento não podem ser alterados ou apagados.';
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER reformas_diario_imutavel
  BEFORE UPDATE OR DELETE ON reformas_registroandamento
  FOR EACH ROW EXECUTE FUNCTION reformas_diario_imutavel();
"""
DESFAZER = """
DROP TRIGGER IF EXISTS reformas_diario_imutavel ON reformas_registroandamento;
DROP FUNCTION IF EXISTS reformas_diario_imutavel();
"""


def aplicar(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(CRIAR)


def reverter(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(DESFAZER)


class Migration(migrations.Migration):
    dependencies = [("reformas", "0001_initial")]
    operations = [migrations.RunPython(aplicar, reverter)]
