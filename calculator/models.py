from django.conf import settings
from django.db import models  # type: ignore

CALCULATOR_LABELS = {
    'kokeb_calculator': 'ኮከብ ስሌት',
    'wealth_calculator': 'የሃብት እጣ ፈንታ',
    'behavior_calculator': 'ስለ ጠባይ',
    'place_calculator': 'መኖሪያ ቦታ',
    'marriage_luck': 'ትዳር በረከት',
    'servant_behavior': 'ሰራተኛ ጸባይ',
    'born_prophecy_calculator': 'የልጅ ስሌት',
    'love_prophecy_calculator': 'ፍቅር ትንቢት',
    'pregnancy_prophecy_calculator': 'ፅንስ ትንቢት',
    'military_prophecy_calculator': 'ጦርነት ትንቢት',
    'life_luck_calculator': 'የህይወት እድል',
    'patient_prophecy_calculator': 'በሽተኛ ትንቢት',
    'legal_calculator': 'ፍርድ ውሳኔ',
    'enemy_behavior_calculator': 'ጠላት ጸባይ',
    'marriage_length': 'ትዳር ቆይታ',
}


class Users(models.Model):
    """Legacy kokeb records — no longer written; kept for existing data."""
    selfname = models.CharField(max_length=100)
    mothersname = models.CharField(max_length=100)
    sign = models.CharField(max_length=100)
    description = models.CharField(default='', max_length=10000)


class CalculationRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calculation_records',
    )
    calculator_type = models.CharField(max_length=64)
    inputs = models.JSONField(default=dict)
    result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def calculator_label(self):
        return CALCULATOR_LABELS.get(self.calculator_type, self.calculator_type)

    @property
    def inputs_display(self):
        if not self.inputs:
            return ''
        return ' · '.join(f'{k}: {v}' for k, v in self.inputs.items() if v)


class Message_After_Transaction(models.Model):
    username = models.CharField(max_length=100)
    transaction_number = models.CharField(max_length=100)
    status = models.CharField(max_length=100,default='denied')
class Allowed_Users(models.Model):
    username = models.CharField(max_length=100)
    status = models.CharField(max_length=100)