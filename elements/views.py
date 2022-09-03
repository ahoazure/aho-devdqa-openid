from django.shortcuts import render # This is a default import
from rest_framework import viewsets
from rest_framework import (generics,permissions,
    renderers,)
from rest_framework.permissions import DjangoModelPermissions

from commoninfo.permissions import IsOwnerOrReadOnly,CustomDjangoModelPermissions
from elements.models import (StgDataElement, FactDataElement)
from elements.serializers import (
    StgDataElementSerializer, FactDataElementSerializer)


class StgDataElementViewSet(viewsets.ModelViewSet):
    queryset = StgDataElement.objects.all()
    serializer_class = StgDataElementSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

class FactDataElementViewSet(viewsets.ModelViewSet):
    serializer_class = FactDataElementSerializer
    permission_classes = (permissions.IsAuthenticated,
        IsOwnerOrReadOnly,CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        queryset = FactDataElement.objects.filter(
                    location__translations__language_code=language).order_by(
                    'location__translations__name').distinct()
        user = self.request.user.id
        groups = list(self.request.user.groups.values_list('user', flat=True))
        location = self.request.user.location_id
        if self.request.user.is_superuser:
            qs=queryset
        elif user in groups: # Match fact location field to that of logged user
            qs=queryset.filter(location=location)
        else:
            qs=queryset.filter(user=user)
        return qs
