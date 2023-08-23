from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from rest_framework import viewsets
from rest_framework import (generics,permissions,renderers,)
from rest_framework.decorators import api_view # new
from rest_framework.response import Response # new
from rest_framework.reverse import reverse # new

from commoninfo.permissions import IsOwnerOrReadOnly,CustomDjangoModelPermissions
from . serializers import (StgDatasourceSerializer,
    StgDisagregationOptionsSerializer,StgDisagregationCategorySerializer,
    StgValueDatatypeSerializer,StgMeasuremethodSerializer,)
from .models import (StgDatasource,StgCategoryParent, StgCategoryoption,
    StgValueDatatype,StgMeasuremethod,)
from django.conf import settings


class StgDisagregationCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = StgDisagregationCategorySerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgCategoryParent.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()

class StgDisagregationOptionsViewSet(viewsets.ModelViewSet):
    serializer_class = StgDisagregationOptionsSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgCategoryoption.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class StgDatasourceViewSet(viewsets.ModelViewSet):
    queryset = StgDatasource.objects.all()
    serializer_class = StgDatasourceSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgDatasource.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class StgValueDatatypeViewSet(viewsets.ModelViewSet):
    serializer_class = StgValueDatatypeSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgValueDatatype.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class StgMeasuremethodViewSet(viewsets.ModelViewSet):
    serializer_class = StgMeasuremethodSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgMeasuremethod.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()

#This code is for the login page
context = {}
def index(request):
    return render(request, 'index.html', context=context)

def login_view(request):
    if not request.POST.get('username') or not request.POST.get('password'):
        return render(request, 'index.html', context=context)
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        # request.session['language'] = request.POST['language']
        return redirect('admin:index') # Changed 25/10/2020 for multi-lingo login
    else:
        return render(
            request, 'index.html', {
                    'error_message': 'Login Failed! \
                    Please enter Valid Username and Password.', })

# Methods for custom error handlers that serve htmls in templates/home/errors
def handler404(request, exception):
    context = {}
    response = render(request, "errors/404.html", context=context)
    response.status_code = 404
    return response

def handler500(request):
    context = {}
    response = render(request, "errors/500.html", context=context)
    response.status_code = 500
    return response
