from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel,Unit
from apps.requests_center.models import AdministrativeRequest
class Vehicle(TimeStampedModel):
 plate=models.CharField(max_length=10,unique=True); brand=models.CharField(max_length=60); model=models.CharField(max_length=80); year=models.PositiveSmallIntegerField(null=True,blank=True)
 unit=models.ForeignKey(Unit,on_delete=models.PROTECT,null=True,blank=True); odometer=models.PositiveIntegerField(default=0); status=models.CharField(max_length=20,default="AVAILABLE")
 def __str__(self): return f"{self.plate} - {self.model}"
class VehicleReservation(TimeStampedModel):
 request=models.OneToOneField(AdministrativeRequest,on_delete=models.PROTECT,related_name="vehicle_reservation"); vehicle=models.ForeignKey(Vehicle,on_delete=models.PROTECT,related_name="reservations")
 driver=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT); destination=models.CharField(max_length=180); starts_at=models.DateTimeField(); ends_at=models.DateTimeField(); initial_odometer=models.PositiveIntegerField(null=True,blank=True); final_odometer=models.PositiveIntegerField(null=True,blank=True)
 @property
 def distance(self): return max(0,(self.final_odometer or 0)-(self.initial_odometer or 0))
