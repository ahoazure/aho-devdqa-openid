from rest_framework.serializers import (HyperlinkedModelSerializer,
    ModelSerializer, ReadOnlyField, DecimalField)
from parler_rest.serializers import TranslatableModelSerializer
from parler_rest.fields import TranslatedFieldsField
from django.shortcuts import get_object_or_404

from health_services.models import (HealthServices_DataIndicators,)
from authentication.models import CustomUser # for filtering logged in instances

# This clas overrides the decimal field in order to round off the decimal places.
class RoundedDecimalField(DecimalField):
    def validate_precision(self, value):
        return value

# Force import wizard to ignore the decimal places and required validation to allow null
class HealthServicesFactSerializer(ModelSerializer):
    location_name = ReadOnlyField(source='location.name')
    numerator_value = RoundedDecimalField(
        max_digits=20,decimal_places=3,required=False,allow_null=True)
    denominator_value = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=False,allow_null=True)
    value_received = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=True,allow_null=False)
    min_value = RoundedDecimalField(
        max_digits=20,decimal_places=3,required=False,allow_null=True)
    max_value = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=False,allow_null=True)
    target_value = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=False,allow_null=True)

    def process_foreign_keys(self, validated_data):
        # Gets the id of logged in user to be supplied to the user foreign key
        user = self.context['request'].user.id
        user = get_object_or_404(CustomUser,id=user)
        validated_data['user'] = user
        return validated_data

    def create(self, validated_data):
        # Create a Facility instance routed from POST via DRF's serializer """
        validated_data = self.process_foreign_keys(validated_data)
        return HealthServices_DataIndicators.objects.create(**validated_data)

    class Meta:
        model = HealthServices_DataIndicators
        fields = [
            'uuid','fact_id','indicator', 'location','location_name','categoryoption',
            'datasource','measuremethod','numerator_value','denominator_value',
            'value_received','value_calculated','min_value','max_value','target_value',
            'periodicity','start_period','end_period','period',]

        data_wizard = {
            'header_row': 0,
            'start_row': 1,
            'show_in_list': True,
        }
