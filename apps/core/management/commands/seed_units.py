from django.core.management.base import BaseCommand
from apps.core.models import Unit
UNITS=[("UAD","Unidade Administrativa"),("PA 00","Sede"),("PA 01","Buena Vista"),("PA 04","Secovi"),("PA 06","Buritis"),("PA 07","Nova Suíça"),("PA 08","Varjão"),("PA 09","Bela Vista"),("PA 10","SMP4"),("PA 11","Cristianópolis"),("PA 12","Educação"),("PA 13","Pecuária"),("PA 14","Vianópolis"),("PA 15","Fecomércio")]
class Command(BaseCommand):
 help="Cadastra unidades iniciais sem informação de lotação."
 def handle(self,*args,**kwargs):
  for code,name in UNITS: Unit.objects.update_or_create(code=code,defaults={"name":name,"active":True})
  self.stdout.write(self.style.SUCCESS(f"{len(UNITS)} unidades processadas."))
