from rest_framework.serializers import (ReadOnlyField, Serializer,
    DecimalField,ModelSerializer,HyperlinkedModelSerializer,)
from parler_rest.serializers import TranslatableModelSerializer
from parler_rest.fields import TranslatedFieldsField
from django.shortcuts import get_object_or_404

from elements.models import (StgDataElement, FactDataElement)
from authentication.models import CustomUser # for filtering logged in instances

class StgDataElementSerializer(TranslatableModelSerializer,HyperlinkedModelSerializer):
    translations = TranslatedFieldsField(shared_model=StgDataElement)
    class Meta:
        model = StgDataElement
        fields = ['dataelement_id','code','aggregation_type','translations']


# This class overrides the decimal field in order to round off the decimal places.
class RoundedDecimalField(DecimalField):
    def validate_precision(self, value):
        return value

# Force import wizard to ignore the decimal places and required validation to allow null
class FactDataElementSerializer(ModelSerializer,):
    location_name = ReadOnlyField(source='location.name')
    value = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=True,allow_null=False)
    target_value = RoundedDecimalField(
        max_digits=20,decimal_places=3,required=False,allow_null=True)

    def process_foreign_keys(self, validated_data):
        # Gets the id of logged in user to be supplied to the user foreign key
        user = self.context['request'].user.id
        user = get_object_or_404(CustomUser,id=user)
        validated_data['user'] = user
        return validated_data

    def create(self, validated_data):
        # Create a Facility instance routed from POST via DRF's serializer """
        validated_data = self.process_foreign_keys(validated_data)
        return FactDataElement.objects.create(**validated_data)

    class Meta:
        model = FactDataElement
        fields = [
            'uuid','fact_id','dataelement','location','location_name',
            'categoryoption','datasource','valuetype','value','target_value',
            'start_year','end_year','period','comment']
