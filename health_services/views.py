from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import (generics,permissions,
    renderers,)

from commoninfo.permissions import (IsOwnerOrReadOnly,
    CustomDjangoModelPermissions)
from health_services.models import (HealthServices_DataIndicators,)
from health_services.serializers import (HealthServicesFactSerializer,)
from regions.models import StgLocation,StgLocationLevel


class HealthServicesFactViewSet(viewsets.ModelViewSet):
    queryset = HealthServices_DataIndicators.objects.all()
    serializer_class = HealthServicesFactSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,IsOwnerOrReadOnly)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        queryset = HealthServices_DataIndicators.objects.filter(
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
