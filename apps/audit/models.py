from django.conf import settings
from django.db import models
class AuditEvent(models.Model):
 created_at=models.DateTimeField(auto_now_add=True); actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True); module=models.CharField(max_length=60); action=models.CharField(max_length=80); object_type=models.CharField(max_length=80,blank=True); object_id=models.CharField(max_length=80,blank=True); ip_address=models.GenericIPAddressField(null=True,blank=True); details=models.JSONField(default=dict,blank=True)
 class Meta: ordering=["-created_at"]
