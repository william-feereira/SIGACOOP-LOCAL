from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel,Unit,CostCenter
class BankAccount(TimeStampedModel):
 owner=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="reimbursement_account"); bank=models.CharField(max_length=80); branch=models.CharField(max_length=20); account=models.CharField(max_length=30); pix_key=models.CharField(max_length=140,blank=True)
class TravelRequest(TimeStampedModel):
 requester=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT); unit=models.ForeignKey(Unit,on_delete=models.PROTECT); cost_center=models.ForeignKey(CostCenter,on_delete=models.PROTECT,null=True,blank=True)
 destination=models.CharField(max_length=180); travel_date=models.DateField(); mileage_km=models.DecimalField(max_digits=10,decimal_places=2); fuel_price=models.DecimalField(max_digits=8,decimal_places=3); average_consumption=models.DecimalField(max_digits=7,decimal_places=2)
 reimbursement=models.DecimalField(max_digits=12,decimal_places=2,editable=False,default=0); status=models.CharField(max_length=20,default="PENDING"); approver_comment=models.TextField(blank=True)
 def calculate(self):
  if self.average_consumption<=0: raise ValueError("Consumo médio deve ser maior que zero")
  return ((self.mileage_km/self.average_consumption)*self.fuel_price).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
 def save(self,*args,**kwargs): self.reimbursement=self.calculate(); super().save(*args,**kwargs)
