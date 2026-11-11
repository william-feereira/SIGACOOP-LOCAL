from django.db import models
from apps.core.models import TimeStampedModel,Unit
class Supplier(TimeStampedModel):
 name=models.CharField("nome",max_length=160); document=models.CharField("CNPJ/CPF",max_length=20,unique=True); active=models.BooleanField("ativo",default=True)
 especialidade=models.CharField(max_length=120,blank=True,help_text="Ex.: elétrica, lógica, pintura, ar-condicionado")
 contato=models.CharField("pessoa de contato",max_length=120,blank=True); telefone=models.CharField(max_length=30,blank=True); email=models.EmailField("e-mail",blank=True)
 class Meta: verbose_name="fornecedor"; verbose_name_plural="fornecedores"; ordering=["name"]
 def __str__(self): return self.name
class Contract(TimeStampedModel):
 number=models.CharField(max_length=50,unique=True); title=models.CharField(max_length=180); supplier=models.ForeignKey(Supplier,on_delete=models.PROTECT); units=models.ManyToManyField(Unit,blank=True); starts_on=models.DateField(); ends_on=models.DateField(); monthly_value=models.DecimalField(max_digits=14,decimal_places=2,null=True,blank=True); status=models.CharField(max_length=20,default="ACTIVE")
 def __str__(self): return f"{self.number} - {self.title}"
