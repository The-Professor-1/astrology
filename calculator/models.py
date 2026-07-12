from django.conf import settings
from django.db import models  # type: ignore

from calculator.labels import CALCULATOR_LABELS

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