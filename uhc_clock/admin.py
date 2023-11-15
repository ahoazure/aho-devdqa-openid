from django.contrib import admin
from django import forms
from django.conf import settings # allow import of projects settings at the root
from django.utils.translation import gettext_lazy as _
from django.forms import BaseInlineFormSet,ValidationError
from parler.admin import (TranslatableAdmin,TranslatableStackedInline,
    TranslatableInlineModelAdmin)
import data_wizard # Solution to data import madness that had refused to go
from itertools import groupby #additional import for managing grouped dropdowm
from import_export.admin import (ImportExportModelAdmin,ExportMixin,
    ExportActionMixin,ImportMixin,ImportExportActionModelAdmin,
    ExportActionModelAdmin,)
from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter,
    RelatedOnlyDropdownFilter) #custom
from django.contrib.admin.views.main import ChangeList
from indicators.serializers import FactDataIndicatorSerializer
from django.forms.models import ModelChoiceField, ModelChoiceIterator

from .models import StgUHCIndicatorGroup,Facts_UHC_DatabaseView
from django.forms import TextInput,Textarea # customize textarea row and column size
from commoninfo.admin import (OverideImportExport,OverideExport,OverideImport,)
from commoninfo.fields import RoundingDecimalFormField # For fixing rounded decimal
from regions.models import StgLocation,StgLocationLevel
from authentication.models import CustomUser, CustomGroup
from home.models import ( StgDatasource,StgCategoryoption,StgMeasuremethod)

from commoninfo.wizard import DataWizardFactIndicatorSerializer
from django.db.models import Case, When
from django.urls import path

from commoninfo.admin_filters import  (
    LocationFilter,IndicatorsFilter,DatasourceFilter,
    CategoryOptionFilter) # added 1/2/2023
from regions.views import LocationSearchView
from indicators.views import IndicatorSearchView
from home.views import CategoryOptionSearchView,DataourceSearchView


@admin.register(StgUHCIndicatorGroup)
class IndicatorDomainAdmin(TranslatableAdmin,OverideExport):
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).filter(
                    indicators__translations__language_code=language).order_by(
                        'translations__name').distinct()
        return qs

    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    fieldsets = (
        ('Domain Attributes', {
                'fields': ('name', 'shortname',)
            }),
            ('Domain Description', {
                'fields': ('description','indicators'),
            }),
        )
    # resource_class = DomainResourceExport
    # actions = ExportActionModelAdmin.actions
    list_display=('name','code','shortname',)
    # list_select_related = ('parent',)
    list_display_links = ('code', 'name',)
    search_fields = ('translations__name','translations__shortname','code')
    list_per_page = 50 #limit records displayed on admin site to 40
    filter_horizontal = ('indicators',) # this should display  inline with multiselect
    exclude = ('date_created','date_lastupdated',)
 

@admin.register(Facts_UHC_DatabaseView)
class Facts_DataViewAdmin(OverideExport):
    change_list_template = 'admin/data_quality/change_list.html' # add buttons for validations
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'105'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request).distinct()
        groups = list(request.user.groups.values_list(
            'user', flat=True))
        user = request.user.id  
        location = request.user.location_id
        language = request.LANGUAGE_CODE 
        db_locations = StgLocation.objects.get(
            location_id=location) #filter by logged user loaction
        
        if request.user.is_superuser:
            qs=qs # show all records if logged in as super user
        elif user in groups: # return records on if the user belongs to the group
            qs=qs.filter(location=db_locations) # return records for logged in country
        else: # return records belonging to logged user only
            qs=qs.filter(user=user)      
        return qs # must return filter queryset to be displayed on admin interface

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, extra_context=None):
        ''' Customize add/edit form '''
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context["show_save"] = False
        extra_context['show_close'] = True
        return super(Facts_DataViewAdmin, self).change_view(
            request,object_id,extra_context=extra_context)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)

    # exclude = ('user',)
    list_display=('uhc_theme','indicator_code','indicator_name','location','categoryoption',
        'datasource','value_received','period','comment')

    list_display_links = ('uhc_theme','indicator_name','datasource',)
    search_fields = ('uhc_theme','indicator_name','location','period','indicator_name') 
    list_per_page = 50 #limit records displayed on admin site to 30

    list_filter = (
        ('uhc_theme',DropdownFilter),
        ('location',DropdownFilter,),
        ('datasource', DropdownFilter,),
        ('period',DropdownFilter),
        ('categoryoption', DropdownFilter,),
    )
