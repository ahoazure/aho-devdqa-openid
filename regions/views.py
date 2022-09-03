from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import (generics,permissions,renderers,)

from commoninfo.permissions import IsOwnerOrReadOnly,CustomDjangoModelPermissions
from .models import (StgWorldbankIncomegroups,StgLocationLevel,
    StgEconomicZones, StgLocation)
from regions.serializers import (StgLocationLevelSerializer,
    StgEconomicZonesSerializer,StgWorldbankIncomegroupsSerializer,
    StgLocationSerializer,)

class StgLocationLevelViewSet(viewsets.ModelViewSet):
    serializer_class = StgLocationLevelSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgLocationLevel.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()



class StgEconomicZonesViewSet(viewsets.ModelViewSet):
    serializer_class = StgEconomicZonesSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgEconomicZones.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class StgWorldbankIncomegroupsViewSet(viewsets.ModelViewSet):
    serializer_class = StgWorldbankIncomegroupsSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgWorldbankIncomegroups.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()



class StgLocationViewSet(viewsets.ModelViewSet):
    serializer_class = StgLocationSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgLocation.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
