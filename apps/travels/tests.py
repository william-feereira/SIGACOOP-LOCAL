from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.core.models import Unit
from .models import TravelRequest
class TravelCalculationTest(TestCase):
 def test_round_half_up(self):
  u=get_user_model().objects.create_user("teste"); unit=Unit.objects.create(code="T",name="Teste")
  t=TravelRequest(requester=u,unit=unit,destination="X",travel_date="2026-10-30",mileage_km=Decimal("1"),average_consumption=Decimal("8"),fuel_price=Decimal("1"))
  self.assertEqual(t.calculate(),Decimal("0.13"))
