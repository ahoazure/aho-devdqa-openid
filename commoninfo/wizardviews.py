from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import (generics,permissions,renderers,)

from commoninfo.permissions import IsOwnerOrReadOnly,CustomDjangoModelPermissions
from facilities.models import StgHealthFacility
from indicators.models import FactDataIndicator
from health_workforce.models import StgHealthWorkforceFacts
from health_services.models import HealthServices_DataIndicators
from elements.models import FactDataElement

from .wizard import (DataWizardFacilitySerializer,DataWizardFactIndicatorSerializer,
    DataWizardWorkforceFactsSerializer,DataWizardElementSerializer,
    DataWizardHealthServicesFactSerializer,)


"""
Custom viewset class for importing health facilities  using django-data-wizard.
We override get_queryset method to fielter serialized data based on logged user
"""
class StgHealthFacilityViewSet(viewsets.ModelViewSet):
    queryset = StgHealthFacility.objects.all()
    serializer_class = DataWizardFacilitySerializer
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



"""
Custom viewset class for importing indicator facts using django-data-wizard. We
override get_queryset method to fielter serialized data based on logged user
"""
class FactDataIndicatorViewSet(viewsets.ModelViewSet):
    queryset = FactDataIndicator.objects.all()
    serializer_class = DataWizardFactIndicatorSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,IsOwnerOrReadOnly)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        queryset = FactDataIndicator.objects.filter(
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


    """
    Custom viewset class for importing workforce facts using django-data-wizard.
    We override get_queryset method to fielter serialized data based on logged user
    """
    class  StgHealthWorkforceFactsViewSet(viewsets.ModelViewSet):
        serializer_class = DataWizardHealthServicesFactSerializer
        permission_classes = (permissions.IsAuthenticated,
            CustomDjangoModelPermissions,IsOwnerOrReadOnly)

        def get_queryset(self):
            language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
            queryset = HealthServices_DataIndicators.objects.filter(
                        location__translations__language_code=language).order_by(
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


"""
Custom viewset class for importing data element facts using django-data-wizard.
We override get_queryset method to fielter serialized data based on logged user
"""
class FactDataElementViewSet(viewsets.ModelViewSet):
    serializer_class = DataWizardElementSerializer
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
