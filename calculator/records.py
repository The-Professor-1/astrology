"""Persist calculator runs for logged-in users only."""
from types import SimpleNamespace

from .models import CalculationRecord


def record_calculation(request, calculator_type, inputs, result):
    """Save a calculation to the database only when the user has an account."""
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return
    if result is None:
        return
    clean_inputs = {k: str(v).strip() for k, v in (inputs or {}).items() if v is not None and str(v).strip()}
    CalculationRecord.objects.create(
        user=request.user,
        calculator_type=calculator_type,
        inputs=clean_inputs,
        result=str(result)[:10000],
    )


def kokeb_result(sign):
    """Lightweight result object for templates (no DB row)."""
    return SimpleNamespace(sign=sign)
