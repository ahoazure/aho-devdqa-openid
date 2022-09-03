from parler_rest.serializers import TranslatableModelSerializer
from parler_rest.fields import TranslatedFieldsField
from django.shortcuts import get_object_or_404
from rest_framework.serializers import (ModelSerializer, ReadOnlyField)

from .models import (StgInstitutionProgrammes,StgTrainingInstitution,
    StgHealthCadre,StgHealthWorkforceFacts,StgInstitutionType,)
from authentication.models import CustomUser # for filtering logged in instances


class StgInstitutionProgrammesSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=StgInstitutionProgrammes)

    class Meta:
        model = StgInstitutionProgrammes
        fields = ['uuid','code','translations']


class StgInstitutionTypeSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=StgInstitutionType)

    class Meta:
        model = StgInstitutionType
        fields = ['uuid','code','translations']


class StgTrainingInstitutionSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=StgTrainingInstitution)

    class Meta:
        model = StgTrainingInstitution
        fields = ['uuid', 'code','location','type','programmes','translations']


class StgHealthCadreSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=StgHealthCadre)

    class Meta:
        model = StgHealthCadre
        fields = ['uuid', 'code','parent','translations']


class StgHealthWorkforceFactsSerializer(ModelSerializer):
    location_name = ReadOnlyField(source='location.name')

    def process_foreign_keys(self, validated_data):
        # Gets the id of logged in user to be supplied to the user foreign key
        user = self.context['request'].user.id
        user = get_object_or_404(CustomUser,id=user)
        validated_data['user'] = user
        return validated_data

    def create(self, validated_data):
        # Create a Facility instance routed from POST via DRF's serializer """
        validated_data = self.process_foreign_keys(validated_data)
        return StgHealthWorkforceFacts.objects.create(**validated_data)

    class Meta:
        model = StgHealthWorkforceFacts

        fields = ('uuid','cadre','location','location_name','categoryoption',
                    'datasource','measuremethod','value', 'start_year',
                    'end_year','period','status',)

        data_wizard = {
        'header_row': 0,
        'start_row': 1,
        'show_in_list': True,
    }
