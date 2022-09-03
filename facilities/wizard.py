from rest_framework import serializers
from django.shortcuts import get_object_or_404
import data_wizard
from .models import StgHealthFacility
from indicators.models import FactDataIndicator

from authentication.models import CustomUser # for filtering logged in instances


"""
This data wizard cusatom class creates facility instance based on the logged user.
To make this posssible, the user foreign key must made read-only.This behaviour
successfuly was implemented on 27/09/2021 after 2 weeks of struggling.
"""
class DataWizardFacilitySerializer(serializers.ModelSerializer):
    location_name = serializers.ReadOnlyField(source='location.location.name')

    """
    Fetch id of logged user supplied via data_wizard run contect.This issue
    was resolved after 3 weeks of intense efforts until I read Dejmail issue
    posted on https://githubmemory.com/repo/wq/django-data-wizard/issues/32
    """
    def process_foreign_keys(self, validated_data):
        # Try direct access to logged user id supplied via API clients
        user = self.context.get('data_wizard').get('run').user.id # magic solution
        user = get_object_or_404(CustomUser,id=user) # create filter based on user id
        validated_data['user'] = user # assign user id to validated data user key
        return validated_data # Now pass clean data to the overriden create() method

    def create(self, validated_data):
        # Create a facility instance based after receiving validated data
        validated_data = self.process_foreign_keys(validated_data)
        return StgHealthFacility.objects.create(**validated_data)

    class Meta:
        model = StgHealthFacility
        read_only_fields = ('user',) # Disable user get from logged user instance
        fields = ('uuid','code','type','location','location_name','owner','name',
                    'shortname','admin_location', 'description','latitude',
                    'longitude','altitude','geosource','url','status','user')

        data_wizard = {
        'header_row': 0,
        'start_row': 1,
        'show_in_list': True,
        'idmap': data_wizard.idmap.existing,
    }
