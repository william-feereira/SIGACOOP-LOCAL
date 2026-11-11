import uuid
from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel,Unit,Department,CostCenter
class AdministrativeRequest(TimeStampedModel):
 class Category(models.TextChoices): VEHICLE="VEHICLE","Veículo"; PURCHASE="PURCHASE","Compra"; SERVICE="SERVICE","Serviço"; MAINTENANCE="MAINTENANCE","Manutenção"; TRAVEL="TRAVEL","Viagem"; ASSET="ASSET","Ativo"; OTHER="OTHER","Outros"
 class Status(models.TextChoices): DRAFT="DRAFT","Rascunho"; PENDING="PENDING","Aguardando validação"; ANALYSIS="ANALYSIS","Em análise"; APPROVAL="APPROVAL","Aguardando aprovação"; EXECUTION="EXECUTION","Em execução"; ACCEPTANCE="ACCEPTANCE","Aguardando aceite"; DONE="DONE","Concluída"; REJECTED="REJECTED","Rejeitada"; CANCELLED="CANCELLED","Cancelada"
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); protocol=models.CharField(max_length=30,unique=True,blank=True)
 requester=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="administrative_requests"); requester_department=models.ForeignKey(Department,on_delete=models.PROTECT,null=True,blank=True)
 beneficiary_unit=models.ForeignKey(Unit,on_delete=models.PROTECT,related_name="beneficiary_requests"); cost_center=models.ForeignKey(CostCenter,on_delete=models.PROTECT,null=True,blank=True)
 category=models.CharField(max_length=20,choices=Category.choices); title=models.CharField(max_length=180); description=models.TextField(); justification=models.TextField(blank=True)
 priority=models.CharField(max_length=12,choices=[("LOW","Baixa"),("NORMAL","Normal"),("HIGH","Alta"),("URGENT","Urgente")],default="NORMAL")
 status=models.CharField(max_length=20,choices=Status.choices,default=Status.DRAFT); estimated_value=models.DecimalField(max_digits=14,decimal_places=2,null=True,blank=True)
 assigned_to=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,null=True,blank=True,related_name="assigned_requests"); due_date=models.DateField(null=True,blank=True)
 def save(self,*args,**kwargs):
  if not self.protocol:
   from django.utils import timezone
   self.protocol=f"SIGA-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
  super().save(*args,**kwargs)
 def __str__(self): return f"{self.protocol} - {self.title}"
class RequestEvent(TimeStampedModel):
 request=models.ForeignKey(AdministrativeRequest,on_delete=models.CASCADE,related_name="events"); actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
 action=models.CharField(max_length=60); from_status=models.CharField(max_length=20,blank=True); to_status=models.CharField(max_length=20,blank=True); comment=models.TextField(blank=True)
