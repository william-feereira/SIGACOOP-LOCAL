from django.db import models
from apps.core.models import TimeStampedModel,Unit,Department
class Asset(TimeStampedModel):
 patrimony=models.CharField(max_length=50,unique=True); name=models.CharField(max_length=150); category=models.CharField(max_length=80); unit=models.ForeignKey(Unit,on_delete=models.PROTECT); department=models.ForeignKey(Department,on_delete=models.PROTECT,null=True,blank=True); status=models.CharField(max_length=30,default="IN_USE"); purchase_value=models.DecimalField(max_digits=14,decimal_places=2,null=True,blank=True); warranty_end=models.DateField(null=True,blank=True)
 def __str__(self): return f"{self.patrimony} - {self.name}"
