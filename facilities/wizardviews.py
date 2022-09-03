from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import (generics,permissions,renderers,)

from commoninfo.permissions import IsOwnerOrReadOnly,CustomDjangoModelPermissions

from .models import StgHealthFacility
from indicators.models import FactDataIndicator
from .wizard import DataWizardFacilitySerializer
from .wizard import DataWizardFacilitySerializer


class StgHealthFacilityViewSet(viewsets.ModelViewSet):
    queryset = StgHealthFacility.objects.all()
    serializer_class = StgHealthFacilitySerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,IsOwnerOrReadOnly)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        queryset = StgHealthFacility.objects.filter(
            location__location__translations__language_code=language).order_by(
            'location__translations__name').distinct()
        user = self.request.user.id
        groups = list(self.request.user.groups.values_list('user',flat=True))
        location = self.request.user.location_id
        if self.request.user.is_superuser:
            qs=queryset
        elif user in groups: # Match fact location field to that of logged user
            qs=queryset.filter(location=location)
        else:
            qs=queryset.filter(user=user)
        return qs
