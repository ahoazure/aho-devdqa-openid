from parler_rest.serializers import TranslatableModelSerializer
from parler_rest.fields import TranslatedFieldsField
from rest_framework.serializers import (ModelSerializer,ReadOnlyField,
    SerializerMethodField)
from django.shortcuts import get_object_or_404

from .models import (StgHealthFacility,StgFacilityType,StgFacilityOwnership,
    StgServiceDomain,FacilityServiceAvailability,FacilityServiceProvision,
    FacilityServiceReadiness,)
from authentication.models import CustomUser # for filtering logged in instances


class StgFacilityTypeSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=StgFacilityType)

    class Meta:
        model = StgFacilityType
        fields = ['uuid','code','translations']


class StgFacilityOwnershipSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=StgFacilityOwnership)

    class Meta:
        model = StgFacilityOwnership
        fields = ['uuid', 'code','location','translations']


class StgServiceDomainSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=StgServiceDomain)

    class Meta:
        model = StgServiceDomain
        fields = ['uuid', 'code','category','level','parent','translations']


"""
This class was creates a new facility instance based on the logged user.
To make this posssible, the user foreign key must made read-only.
This behaviour was implemented on 21/09/2021 after 2 weeks of struggling.
"""
class StgHealthFacilitySerializer(ModelSerializer):
    location_name = ReadOnlyField(source='location.location.name')

    def process_foreign_keys(self, validated_data):
        # Gets the id of logged in user to be supplied to the user foreign key
        user = self.context['request'].user.id
        user = get_object_or_404(CustomUser,id=user)
        validated_data['user'] = user
        return validated_data

    def create(self, validated_data):
        # Create a Facility instance routed from POST via DRF's serializer """
        validated_data = self.process_foreign_keys(validated_data)
        return StgHealthFacility.objects.create(**validated_data)

    class Meta:
        model = StgHealthFacility
        read_only_fields = ('user',) # Disable user get from logged user instance
        fields = ('uuid','code','type','location','location_name','owner','name',
                    'shortname','admin_location', 'description','latitude',
                    'longitude','altitude','geosource','url','status','user')
                    

class FacilityServiceAvailabilitySerializer(ModelSerializer):

    class Meta:
        model = FacilityServiceAvailability

        fields = ('uuid','code','facility','domain','intervention','service',
        'provided','specialunit','staff','infrastructure','supplies',
        'date_assessed',)

        data_wizard = {
        'header_row': 0,
        'start_row': 1,
        'show_in_list': True,
    }


class FacilityServiceProvisionSerializer(ModelSerializer):

    class Meta:
        model = FacilityServiceProvision

        fields = ('uuid','code','facility','domain','units','available',
        'functional','date_assessed',)

        data_wizard = {
        'header_row': 0,
        'start_row': 1,
        'show_in_list': True,
    }


class FacilityServiceReadinessSerializer(ModelSerializer):

    class Meta:
        model = FacilityServiceReadiness

        fields = ('uuid','code','facility','domain','units','available',
        'require','date_assessed',)


        data_wizard = {
        'header_row': 0,
        'start_row': 1,
        'show_in_list': True,
    }
