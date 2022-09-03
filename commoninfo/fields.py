from django import forms
from django.db import models
from decimal import Decimal

def round_decimal(value, places):
    if value is not None:
        return value.quantize(Decimal(10) ** -places)
    return value

class RoundingDecimalFormField(forms.DecimalField):
    def to_python(self, value):
        value = super(RoundingDecimalFormField, self).to_python(value)
        return round_decimal(value, self.decimal_places)
