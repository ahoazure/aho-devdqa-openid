from django.contrib import admin
from parler.admin import TranslatableAdmin
from django.utils.translation import gettext_lazy as _ #For translating imported verbose_name
from regions.models import StgLocation
from data_wizard.admin import ImportActionModelAdmin
from django.forms import TextInput,Textarea #for customizing textarea row and column size
from .models import FileSources,URLSources #customize import sourece

from commoninfo.admin import OverideImportExport, OverideExport
from .models import (StgCategoryParent,StgCategoryoption,StgMeasuremethod,
    StgValueDatatype,StgDatasource,StgPeriodType,StgCustomNationalObservatory)
from .resources import(DisaggregateCategoryExport,DataSourceExport,
    DisaggregateOptionExport,MeasureTypeExport,DataTypeExport)
from import_export.admin import (ImportExportModelAdmin,
    ImportExportActionModelAdmin,)
from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter,
    RelatedOnlyDropdownFilter) #custom import
from .filters import TranslatedFieldFilter #Danile solution to duplicate filters
from authentication.models import CustomUser


@admin.register(StgPeriodType)
class periodtypeAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'80'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }
    #resource_class = DataTypeExport
    list_display=['name','code','shortname','description',]
    list_display_links = ('code', 'name',)
    search_fields = ('name','code',) #display search field
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)



@admin.register(StgCustomNationalObservatory)
class NHOCustomizationAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'80'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.email
        db_user = CustomUser.objects.get(email=user)

        if request.user.is_superuser:
            return qs
        return qs.filter(user=db_user) # else restrict access to user uploads

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.email
        language = request.LANGUAGE_CODE

        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(email=user)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    """
    Overrride model_save method to grab id of the logged in user. The save_model
    method is given HttpRequest (request), model instance (obj), ModelForm
    instance (form), and boolean value (change) based on add or changes to object.
    """
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set user from request during the first save.
        super().save_model(request, obj, form, change)

    fieldsets = (
        ('Header Details', {
                'fields': ('name','location','custom_header','coat_arms',)
            }),
            ('Contact Details', {
                'fields': ('address','email','phone_part','url',),
            }),
            ('Footer Details', {
                'fields': ('custom_footer',),
            }),
            ('Announcements', {
                'fields': ('announcement',),
            }),
        )

    #resource_class = DataTypeExport
    list_display=['name','location','custom_header','phone_number','url','coat_arms',]
    list_display_links = ('name', 'location','url')
    search_fields = ('name', 'location','url') #display search field
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)



@admin.register(StgCategoryParent)
class DisaggregateCategoryAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs

    resource_class = DisaggregateCategoryExport #for export only
    list_display=['name','code','shortname','description',]
    list_display_links = ('code', 'name',)
    search_fields = ('translations__name', 'translations__shortname','code',)
    list_per_page = 15 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)


@admin.register(StgCategoryoption)
class DisaggregationAdmin(TranslatableAdmin,OverideExport):
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs

    fieldsets = (
        ('Disaggregation Attributes', {
                'fields': ('name','shortname','category',)
            }),
            ('Detailed Description', {
                'fields': ('description',),
            }),
        )
    resource_class = DisaggregateOptionExport #for export only
    list_display=['name','code','shortname','description','category',]
    list_display_links = ('code', 'name',)
    search_fields = ('translations__name', 'translations__shortname',)
    list_per_page = 15 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated',)
    list_filter = (
        ('category',TranslatedFieldFilter,), #Use the comma for inheritance
    )


@admin.register(StgValueDatatype)
class DatatypeAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs

    resource_class = DataTypeExport
    list_display=['name','code','description',]
    list_display_links = ('code', 'name',)
    search_fields = ('translations__name','translations__shortname','code',)
    list_per_page = 15 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)

@admin.register(StgDatasource)
class DatasourceAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs

    fieldsets = (
        ('Data source Attributes', {
                'fields': ('name','shortname','level',)
            }),
            ('Detailed Description', {
                'fields': ('description',),
            }),
        )
    resource_class = DataSourceExport #for export only
    list_display=['name','shortname','code','description','level']
    list_display_links = ('code', 'name',)
    search_fields = ('translations__name', 'translations__shortname',
        'code','translations__level') #display search field
    list_per_page = 50 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated',)
    list_filter = (
        ('translations__level',DropdownFilter,), #Use the comma for inheritance
    )


@admin.register(StgMeasuremethod)
class MeasuredAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs

    resource_class = MeasureTypeExport
    list_display=['name','code','measure_value','description',]
    list_display_links = ('code', 'name',)
    search_fields = ('translations__name','code',) #display search field
    list_per_page = 15 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)

# ------------------------------------------------------------------------------
# The following two admin classes are used to customize the Data_Wizard page.
# The classes overrides admin.py in site-packages/data_wizard/sources/
# ------------------------------------------------------------------------------
class FileSourceAdmin(ImportActionModelAdmin):
    menu_title = _("Upload File... ")
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.email
        db_user = CustomUser.objects.get(email=user)

        if request.user.is_superuser:
            return qs
        return qs.filter(user=db_user) # else restrict access to user uploads

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.email
        language = request.LANGUAGE_CODE
        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocation.objects.all().order_by(
                'location_id')
                # Looks up for the location level upto the country level
            elif user in groups:
                kwargs["queryset"] = StgLocation.objects.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2).order_by(
                'location_id')
            else:
                kwargs["queryset"] = StgLocation.objects.filter(
                location_id=request.user.location_id).translated(
                language_code=language)

        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(email=user)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    """
    Overrride model_save method to grab id of the logged in user. The save_model
    method is given HttpRequest (request), model instance (obj), ModelForm
    instance (form), and boolean value (change) based on add or changes to object.
    """
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set user from request during the first save.
            obj.location = request.user.location # set location during first save.
        super().save_model(request, obj, form, change)

    fieldsets = ( # used to create frameset sections on file import form
        ('File Import Details', {
                'fields': ('name','file','url')
            }),
        )
    list_display=('name','location','url','date',)
admin.site.register(FileSources, FileSourceAdmin)


# This class admin class is used to customize change page for the URL data source
class URLSourceAdmin(ImportActionModelAdmin):
    menu_title = _("Import URL...")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.email
        db_user = CustomUser.objects.get(email=user)

        if request.user.is_superuser:
            return qs
        return qs.filter(user=db_user) # else restrict access to user uploads

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.email
        language = request.LANGUAGE_CODE
        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocation.objects.all().order_by(
                'location_id')
                # Looks up for the location level upto the country level
            elif user in groups:
                kwargs["queryset"] = StgLocation.objects.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2).order_by(
                'location_id')
            else:
                kwargs["queryset"] = StgLocation.objects.filter(
                location_id=request.user.location_id).translated(
                language_code=language)

        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(email=user)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    """
    Overrride model_save method to grab id of the logged in user. The save_model
    method is given HttpRequest (request), model instance (obj), ModelForm
    instance (form), and boolean value (change) based on add or changes to object.
    """
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set user from request during the first save.
            obj.location = request.user.location # set location during first save.
        super().save_model(request, obj, form, change)

    fieldsets = ( # used to create frameset sections on file import form
        ('File Import Details', {
                'fields': ('name','file',)
            }),
        )
    list_display=('name','location','url','date',)
admin.site.register(URLSources,URLSourceAdmin)
