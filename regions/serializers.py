from parler_rest.serializers import TranslatableModelSerializer
from rest_framework.serializers import (ModelSerializer,
        HyperlinkedModelSerializer, HyperlinkedRelatedField)
from .models import (StgLocationLevel, StgEconomicZones, StgLocation,
        StgWorldbankIncomegroups,)


class StgLocationLevelSerializer(TranslatableModelSerializer):
    class Meta:
        model = StgLocationLevel
        fields = ['uuid', 'type', 'name', 'code', 'description']


class StgEconomicZonesSerializer(TranslatableModelSerializer):
    class Meta:
        model = StgEconomicZones
        fields = ['uuid', 'name', 'code', 'shortname', 'description']


class StgWorldbankIncomegroupsSerializer(TranslatableModelSerializer):
    class Meta:
        model = StgWorldbankIncomegroups
        fields = ['uuid', 'name', 'code', 'shortname', 'description']


class StgLocationSerializer(TranslatableModelSerializer):
    class Meta:
        model = StgLocation
        fields = [
            'location_id', 'locationlevel','name', 'iso_alpha','iso_number','code',
            'description', 'parent', 'latitude','longitude','cordinate','wb_income',
            'zone','special']
