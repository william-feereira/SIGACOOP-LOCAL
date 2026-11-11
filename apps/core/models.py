from django.db import models
class TimeStampedModel(models.Model):
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: abstract=True
class Unit(TimeStampedModel):
    code=models.CharField(max_length=20,unique=True); name=models.CharField(max_length=120); active=models.BooleanField(default=True)
    def __str__(self): return f"{self.code} - {self.name}"
class Department(TimeStampedModel):
    unit=models.ForeignKey(Unit,on_delete=models.PROTECT,related_name="departments"); name=models.CharField(max_length=120); active=models.BooleanField(default=True)
    class Meta: unique_together=("unit","name")
    def __str__(self): return f"{self.unit.code} / {self.name}"
class CostCenter(TimeStampedModel):
    code=models.CharField(max_length=30,unique=True); name=models.CharField(max_length=120); unit=models.ForeignKey(Unit,on_delete=models.PROTECT,related_name="cost_centers")
    def __str__(self): return f"{self.code} - {self.name}"
