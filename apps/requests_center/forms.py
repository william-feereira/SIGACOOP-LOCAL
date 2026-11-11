from django import forms
from .models import AdministrativeRequest
class RequestForm(forms.ModelForm):
 class Meta:
  model=AdministrativeRequest; fields=["beneficiary_unit","requester_department","cost_center","category","title","description","justification","priority","estimated_value","due_date"]
  widgets={"description":forms.Textarea(attrs={"rows":4}),"justification":forms.Textarea(attrs={"rows":3}),"due_date":forms.DateInput(attrs={"type":"date"})}
