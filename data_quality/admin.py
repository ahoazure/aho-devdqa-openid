from django.contrib import admin
from django import forms
from django.conf import settings # allow import of projects settings at the root
from django.forms import BaseInlineFormSet

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
from indicators.models import (StgIndicatorReference,StgIndicator,StgIndicatorDomain,
    FactDataIndicator,IndicatorProxy,AhoDoamain_Lookup,aho_factsindicator_archive,
    StgNarrative_Type,StgAnalyticsNarrative,StgIndicatorNarrative,
    NHOCustomizationProxy,NHOCustomFactsindicator)
from django.forms import TextInput,Textarea # customize textarea row and column size
from commoninfo.admin import (OverideImportExport,OverideExport,OverideImport,)
from commoninfo.fields import RoundingDecimalFormField # For fixing rounded decimal
from regions.models import StgLocation,StgLocationLevel
from authentication.models import CustomUser, CustomGroup
from home.models import ( StgDatasource,StgCategoryoption,StgMeasuremethod)
from indicators.filters import TranslatedFieldFilter #Danile solution to duplicate filters

from .models import (MeasureTypes_Validator,DataSource_Validator,
    CategoryOptions_Validator,Similarity_Index,Mutiple_MeasureTypes,
    Facts_DataFrame,MeasureType_Statistics,DqaInvalidCategoryoptionRemarks,
    DqaInvalidDatasourceRemarks,DqaInvalidMeasuretypeRemarks,
    DqaInvalidPeriodRemarks, DqaExternalConsistencyOutliersRemarks,
    DqaInternalConsistencyOutliersRemarks,DqaValueTypesConsistencyRemarks
    )

class GroupedModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    (self.field.group_label(group),[self.choice(ch) for ch in choices])
                        for group,choices in groupby(self.queryset.all(),
                            key=lambda row: getattr(row, self.field.group_by_field))
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            for group, choices in groupby(self.queryset.all(),
	        key=lambda row: getattr(row, self.field.group_by_field)):
                    yield (self.field.group_label(group),
                        [self.choice(ch) for ch in choices])

class GroupedModelChoiceField(ModelChoiceField):
    def __init__(
        self, group_by_field, group_label=None, cache_choices=False,
        *args, **kwargs):
        """
        group_by_field is the name of a field on the model
        group_label is a function to return a label for each choice group
        """
        super(GroupedModelChoiceField, self).__init__(*args, **kwargs)
        self.group_by_field = group_by_field
        self.cache_choices = cache_choices
        if group_label is None:
            self.group_label = lambda group: group
        else:
            self.group_label = group_label

    def _get_choices(self):
        """
        Exactly as per ModelChoiceField except returns new iterator class
        """
        if hasattr(self, '_choices'):
            return self._choices
        return GroupedModelChoiceIterator(self)
    choices = property(_get_choices, ModelChoiceField._set_choices)
                       
@admin.register(Facts_DataFrame)
class Facts_DataFrameAdmin(OverideExport):
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
        db_locations = StgLocation.objects.get(location_id=location) #filter by logged user loaction

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
        return super(Facts_DataFrameAdmin, self).change_view(
            request,object_id,extra_context=extra_context)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)

    exclude = ('user',)
    list_display=('afrocode','indicator_name','location','categoryoption',
        'datasource','value','period',)

    list_display_links = ('location','indicator_name','location',)
    search_fields = ('indicator_name','location','period','afrocode') 
    list_per_page = 50 #limit records displayed on admin site to 30

    list_filter = (
        ('indicator_name',DropdownFilter),
        ('location',DropdownFilter,),
        ('datasource', DropdownFilter,),
        ('period',DropdownFilter),
        ('categoryoption', DropdownFilter,),
    )


@admin.register(MeasureTypes_Validator)
class MeasureTypeAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)
    list_display=['afrocode','indicator_name', 'measure_type',
        'measuremethod_id',]
    search_fields = ('afrocode','indicator_name','measure_type') 
    list_filter = (
        ('indicator_name', DropdownFilter,),
        ('measure_type',DropdownFilter),
    )


@admin.register(DataSource_Validator)
class MeasureTypeAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)
    list_display=['afrocode','indicator_name', 'datasource',
        'datasource_id',]
    search_fields = ('afrocode','indicator_name','datasource') 
    list_filter = (
        ('indicator_name', DropdownFilter,),
        ('datasource',DropdownFilter),
    )


@admin.register(CategoryOptions_Validator) 
class MeasureTypeAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)
    list_display=['afrocode','indicator_name', 'categoryoption',
        'categoryoption_id',]
    search_fields = ('afrocode','indicator_name','categoryoption') 
    list_filter = (
        ('indicator_name', DropdownFilter,),
        ('categoryoption',DropdownFilter),
    )
     

# @admin.register(MeasureType_Statistics)
# class MeasureTypeStatisticsAdmin(ExportActionModelAdmin,OverideExport):
#     list_display=['location','indicator_name', 'count',]
        

@admin.register(Similarity_Index)
class Similarity_IndexAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

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
        return super(Similarity_IndexAdmin, self).change_view(
            request,object_id,extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)  
    list_display=['source_indicator','similar_indicator', 'score']
    search_fields = ('source_indicator','similar_indicator',) 
    list_filter = (
        ('source_indicator', DropdownFilter,),
        ('score',DropdownFilter),
    )
     

@admin.register(Mutiple_MeasureTypes)
class Mutiple_MeasureTypesAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, extra_context=None):
        ''' Customize add/edit form '''
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context["show_save"] = True
        extra_context['show_close'] = True
        return super(Mutiple_MeasureTypesAdmin, self).change_view(
            request,object_id,extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)   
    list_display=['indicator_name','location', 'categoryoption',
      'datasource','measure_type', 'value','period','remarks', ]
    search_fields = ('indicator_name','location','categoryoption',
      'datasource','measure_type',) 

    list_filter = (
        ('location', DropdownFilter,),
        ('indicator_name', DropdownFilter,),
        ('categoryoption', DropdownFilter,),
        ('datasource', DropdownFilter,),
        ('measure_type', DropdownFilter,),
        ('period', DropdownFilter),
        ('remarks', DropdownFilter),
    )


# ---------------------------data validation interfaces from algorithms 1-4--------------------------------------------
@admin.register(DqaInvalidCategoryoptionRemarks)
class DQAInvalidCategoryOptionsAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request).distinct()
        groups = list(request.user.groups.values_list(
            'user', flat=True))
        user = request.user.id  
        location = request.user.location_id
        language = request.LANGUAGE_CODE 
        db_locations = StgLocation.objects.get(location_id=location) #filter by logged user loaction

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
        return super(DQAInvalidCategoryOptionsAdmin, self).change_view(
            request,object_id,extra_context=extra_context)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)    
    list_display=['indicator_name','location','categoryoption','datasource',
        'measure_type','value','period','check_category_option'] 
    search_fields = ('indicator_name','location','categoryoption',
      'datasource','measure_type',) 
    list_filter = (
        ('location', DropdownFilter,),
        ('indicator_name', DropdownFilter,),
        ('categoryoption', DropdownFilter,),
        ('datasource', DropdownFilter,),
        ('measure_type', DropdownFilter,),
        ('period', DropdownFilter),
    )


@admin.register(DqaInvalidMeasuretypeRemarks)
class DQAInvalidMeasureTypesAdminn(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request).distinct()
        groups = list(request.user.groups.values_list(
            'user', flat=True))
        user = request.user.id  
        location = request.user.location_id
        language = request.LANGUAGE_CODE 
        db_locations = StgLocation.objects.get(location_id=location) #filter by logged user loaction

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
        return super(DQAInvalidMeasureTypesAdminn, self).change_view(
            request,object_id,extra_context=extra_context)
  
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)    
    list_display=['indicator_name','location','categoryoption',
      'datasource','measure_type','value','period','check_mesure_type']  
    search_fields = ('indicator_name','location','categoryoption',
      'datasource','measure_type',)
    list_filter = (
        ('location', DropdownFilter,),
        ('indicator_name', DropdownFilter,),
        ('categoryoption', DropdownFilter,),
        ('datasource', DropdownFilter,),
        ('measure_type', DropdownFilter,),
        ('period', DropdownFilter),
    )


@admin.register(DqaInvalidDatasourceRemarks)
class DQAInvalidDataSourcesAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request).distinct()
        groups = list(request.user.groups.values_list(
            'user', flat=True))
        user = request.user.id  
        location = request.user.location_id
        language = request.LANGUAGE_CODE 
        db_locations = StgLocation.objects.get(location_id=location) #filter by logged user loaction

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
        return super(DQAInvalidDataSourcesAdmin, self).change_view(
            request,object_id,extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)   
    list_display=['indicator_name','location','categoryoption',
        'datasource','measure_type','value','period','check_data_source']
    search_fields = ('indicator_name','location','categoryoption',
      'datasource','measure_type',) 
    list_filter = (
        ('location', DropdownFilter,),
        ('indicator_name', DropdownFilter,),
        ('categoryoption', DropdownFilter,),
        ('datasource', DropdownFilter,),
        ('measure_type', DropdownFilter,),
        ('period', DropdownFilter),
    )


@admin.register(DqaInvalidPeriodRemarks)
class DQAInvalidPeriodAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request).distinct()
        groups = list(request.user.groups.values_list(
            'user', flat=True))
        user = request.user.id  
        location = request.user.location_id
        language = request.LANGUAGE_CODE 
        db_locations = StgLocation.objects.get(location_id=location) #filter by logged user loaction

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
        return super(DQAInvalidPeriodAdmin, self).change_view(
            request,object_id,extra_context=extra_context)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)    
    list_display=['indicator_name','location', 'categoryoption',
      'datasource','measure_type','value','period','check_year']
    search_fields = ('indicator_name','location','categoryoption',
      'datasource','measure_type',)
    list_filter = (
        ('location', DropdownFilter,),
        ('indicator_name', DropdownFilter,),
        ('categoryoption', DropdownFilter,),
        ('datasource', DropdownFilter,),
        ('measure_type', DropdownFilter,),
        ('period', DropdownFilter),
    )


@admin.register(DqaExternalConsistencyOutliersRemarks)
class DQAExternalconsistencyAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request).distinct()
        groups = list(request.user.groups.values_list(
            'user', flat=True))
        user = request.user.id  
        location = request.user.location_id
        language = request.LANGUAGE_CODE 
        db_locations = StgLocation.objects.get(location_id=location) #filter by logged user loaction

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
        return super(DQAExternalconsistencyAdmin, self).change_view(
            request,object_id,extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)    
    list_display=['indicator_name','location', 'categoryoption',
      'datasource','measure_type','value','period','external_consistency']
    search_fields = ('indicator_name','location','categoryoption',
      'datasource','measure_type',)
    list_filter = (
        ('location', DropdownFilter,),
        ('indicator_name', DropdownFilter,),
        ('categoryoption', DropdownFilter,),
        ('datasource', DropdownFilter,),
        ('measure_type', DropdownFilter,),
        ('period', DropdownFilter),
    )


@admin.register(DqaInternalConsistencyOutliersRemarks)
class DQAInternalconsistencyAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request).distinct()
        groups = list(request.user.groups.values_list(
            'user', flat=True))
        user = request.user.id  
        location = request.user.location_id
        language = request.LANGUAGE_CODE 
        db_locations = StgLocation.objects.get(location_id=location) #filter by logged user loaction

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
        return super(DQAInternalconsistencyAdmin, self).change_view(
            request,object_id,extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)    
    list_display=['indicator_name','location', 'categoryoption',
      'datasource','measure_type','value','period','internal_consistency']   
    search_fields = ('indicator_name','location','categoryoption',
      'datasource','measure_type',) 
    list_filter = (
        ('location', DropdownFilter,),
        ('indicator_name', DropdownFilter,),
        ('categoryoption', DropdownFilter,),
        ('datasource', DropdownFilter,),
        ('measure_type', DropdownFilter,),
        ('period', DropdownFilter),
    )


@admin.register(DqaValueTypesConsistencyRemarks)
class DQAValueTypesConsistencyAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request).distinct()
        groups = list(request.user.groups.values_list(
            'user', flat=True))
        user = request.user.id  
        location = request.user.location_id
        language = request.LANGUAGE_CODE 
        db_locations = StgLocation.objects.get(location_id=location) #filter by logged user loaction

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
        return super(DQAValueTypesConsistencyAdmin, self).change_view(
            request,object_id,extra_context=extra_context)
   
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)
    
    exclude = ('user',)  
    list_display=['indicator_name','location', 'categoryoption',
      'datasource','measure_type','value','period','check_value']
    search_fields = ('indicator_name','location','categoryoption',
      'datasource','measure_type',)
    list_filter = (
        ('location', DropdownFilter,),
        ('indicator_name', DropdownFilter,),
        ('categoryoption', DropdownFilter,),
        ('datasource', DropdownFilter,),
        ('measure_type', DropdownFilter,),
        ('period', DropdownFilter),
    )
      