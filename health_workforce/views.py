from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import (generics,permissions,renderers,)

from commoninfo.permissions import IsOwnerOrReadOnly,CustomDjangoModelPermissions
from .models import (StgInstitutionProgrammes,StgTrainingInstitution,
    StgInstitutionType,StgHealthCadre,StgHealthWorkforceFacts,)
from .serializers import (StgInstitutionProgrammesSerializer,
    StgInstitutionTypeSerializer,StgTrainingInstitutionSerializer,
    StgHealthCadreSerializer,StgHealthWorkforceFactsSerializer,)

class StgInstitutionProgrammesViewSet(viewsets.ModelViewSet):
    serializer_class = StgInstitutionProgrammesSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgInstitutionProgrammes.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class StgInstitutionTypeViewSet(viewsets.ModelViewSet):
    serializer_class = StgInstitutionTypeSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgInstitutionType.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class StgTrainingInstitutionViewSet(viewsets.ModelViewSet):
    serializer_class = StgTrainingInstitutionSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,IsOwnerOrReadOnly)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgTrainingInstitution.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class StgHealthCadreViewSet(viewsets.ModelViewSet):
    serializer_class = StgHealthCadreSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,IsOwnerOrReadOnly)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgHealthCadre.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class  StgHealthWorkforceFactsViewSet(viewsets.ModelViewSet):
    serializer_class = StgHealthWorkforceFactsSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,IsOwnerOrReadOnly)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        queryset = StgHealthWorkforceFacts.objects.filter(
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
