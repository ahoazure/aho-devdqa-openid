from django.contrib import admin
from parler.admin import TranslatableAdmin
from django.utils.html import format_html
from django.forms import BaseInlineFormSet
from django.shortcuts import redirect
from django import forms
import data_wizard # Solution to data import madness that had refused to go
from django.conf import settings # allow import of projects settings at the root
from django.forms import TextInput,Textarea #customize textarea row and column size
from import_export.formats import base_formats
from .models import (StgFacilityType,StgFacilityServiceMeasureUnits,
    StgFacilityOwnership,StgHealthFacility,StgServiceDomain,StgLocationCodes,
    FacilityServiceAvailability,FacilityServiceAvailabilityProxy,
    FacilityServiceProvision,StgFacilityServiceIntervention,
    FacilityServiceReadiness,StgFacilityServiceAreas,
    FacilityServiceProvisionProxy,FacilityServiceReadinesProxy)
from commoninfo.admin import OverideImportExport,OverideExport,OverideImport
# from publications.serializers import StgKnowledgeProductSerializer
from .resources import (StgFacilityResourceExport,FacilityTypeResourceExport,
    FacilityServiceDomainResourceExport,StgFacilityServiceAvailabilityExport,
    StgFacilityServiceCapacityExport,StgFacilityServiceReadinessExport,)
from regions.models import StgLocation,StgLocationCodes
from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter,
    RelatedOnlyDropdownFilter) #custom
from import_export.admin import (ImportExportModelAdmin, ExportMixin,
    ImportExportActionModelAdmin,ExportActionModelAdmin,)
from authentication.models import CustomUser, CustomGroup
# from bootstrap_datepicker_plus import DatePickerInput # Nice date picker 06/03
from .filters import TranslatedFieldFilter #Danile solution to duplicate filters

from commoninfo.wizard import DataWizardFacilitySerializer

#Methods used to register global actions performed on data. See actions listbox
def transition_to_pending (modeladmin, request, queryset):
    queryset.update(comment = 'pending')
transition_to_pending.short_description = "Mark selected as Pending"

def transition_to_approved (modeladmin, request, queryset):
    queryset.update (comment = 'approved')
transition_to_approved.short_description = "Mark selected as Approved"

def transition_to_rejected (modeladmin, request, queryset):
    queryset.update (comment = 'rejected')
transition_to_rejected.short_description = "Mark selected as Rejected"


@admin.register(StgFacilityType)
class FacilityTypeAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    """
    Serge requested that a user does not see other users or groups data.
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        return qs

    def get_export_resource_class(self):
        return FacilityTypeResourceExport

    fieldsets = (
        ('Health Facility Type', {
                'fields':('name','shortname','description',) #afrocode may be null
            }),
        )
    list_display=['name','code','shortname','description']
    list_display_links =('code', 'name',)
    search_fields = ('code','translations__name',) #display search field
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)


@admin.register(StgFacilityOwnership)
class FacilityOwnership (TranslatableAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    """
    Serge requested that a user does not see other users or groups data.
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        return qs

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        qs = super().get_queryset(request)
        groups = list(request.user.groups.values_list('user', flat=True))
        language = request.LANGUAGE_CODE
        user = request.user.id
        email = request.user.email
        user_location = request.user.location.location_id
        countrycodes=StgLocationCodes.objects.values_list(
            'country_code',flat=True)
        # This queryset is used to load specific phone code for logged in user
        country_code = countrycodes.filter(location=request.user.location)

        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocationCodes.objects.all().filter(
                location__translations__language_code=language).order_by(
                'location_id')

                # Looks up for the location level upto the country level
            elif user in groups and user_location==1:
                kwargs["queryset"] = StgLocationCodes.objects.filter(
                location__locationlevel__locationlevel_id__gte=1,
                location__locationlevel__locationlevel_id__lte=2).order_by(
                'location_id')
            else:
                kwargs["queryset"] = StgLocationCodes.objects.filter(
                location_id=user_location).order_by('location_id')

        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(email=email)
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
        ('Facility Ownership Details', {
                'fields':('name','shortname','description',) #afrocode may be null
            }),
            ('Facility Ownership Country', {
                'fields': ('location',)
            }),
        )
    list_display=['name','code','shortname','location','description',]
    list_select_related = ('location','user',)
    list_display_links =('code', 'name',)
    search_fields = ('code','translations__name','translations__shortname',) #display search field
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)


class FacilityServiceAvailabilityProxyForm(forms.ModelForm):
    class Meta:
        model = FacilityServiceAvailability
        fields = ('facility','domain','intervention','service','provided',
        'specialunit','staff','infrastructure','supplies','date_assessed',)
        # widgets = {
        #     'date_assessed': DatePickerInput(), # # default date-format %m/%d/%Y will be used
        # }


class FacilityServiceAvailabilityInline(admin.TabularInline):
    """
    Serge requested that a user does not see other users or groups data.
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1:
            qs=qs.filter(user_id=user)
        return qs

    """
    Serge requested that the form for data input be restricted to user's country.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.=== modified 02/02/2021
    """

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        qs = super().get_queryset(request)
        db_sevicedomains = StgServiceDomain.objects.all()
        db_sevicesubdomains=db_sevicedomains.exclude(
            parent_id__isnull=True).filter(category=1)
        if db_field.name == "domain":
            kwargs["queryset"]=db_sevicesubdomains

        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    # form = FacilityServiceAvailabilityProxyForm #overrides the default model form
    model = FacilityServiceAvailability
    # formset = LimitModelFormset
    extra = 1 # Used to control  number of empty rows displayed.
    list_select_related = ('facility','domain','intervention','service',)
    fields = ('facility','domain','intervention','service','provided',
        'specialunit','staff','infrastructure','supplies','date_assessed',)


class FacilityServiceCapacityInline(admin.TabularInline):
    """
    Serge requested that a user does not see other users or groups data.
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1:
            qs=qs.filter(user_id=user)
        return qs

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        db_sevicedomains = StgServiceDomain.objects.all()
        db_sevicesubdomains=db_sevicedomains.exclude(
            parent_id__isnull=True).filter(category=2).filter(
            level='Level 2')
        db_provisionunits=StgFacilityServiceMeasureUnits.objects.select_related(
            'domain') #good
        if db_field.name == "domain":
            kwargs["queryset"]=db_sevicesubdomains
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    model = FacilityServiceProvision
    # formset = LimitModelFormset
    extra = 1 # Used to control  number of empty rows displayed.

    list_select_related = ('facility','domain','units')
    fields = ('facility','domain','units','available','functional',
            'date_assessed',)


class FacilityServiceReadinessInline(admin.TabularInline):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location<=2:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gt=2,
                locationlevel__locationlevel_id__lte=3)
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1:
            qs=qs.filter(user_id=user)
        return qs

    """
    Serge requested that the form for data input be restricted to user's country.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.=== modified 02/02/2021
    """

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        db_sevicedomains = StgServiceDomain.objects.all()
        db_sevicesubdomains=db_sevicedomains.exclude(
            parent_id__isnull=True).filter(category=3).filter(level='level 1')
        db_provisionunits=StgFacilityServiceMeasureUnits.objects.select_related(
            'domain')
        if db_field.name == "domain":
            kwargs["queryset"]=db_sevicesubdomains
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    model = FacilityServiceReadiness
    # formset = LimitModelFormset
    extra = 1 # Used to control  number of empty rows displayed.

    list_select_related = ('facility','domain','units')
    fields = ('facility','domain','units','available','require','date_assessed',)


@admin.register(StgServiceDomain)
class ServiceDomainAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    """
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location<=2:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gt=2,
                locationlevel__locationlevel_id__lte=3)
        return qs

    def get_export_resource_class(self):
        return FacilityServiceDomainResourceExport

    fieldsets = (
        ('Service Domain Attributes', {
                'fields':('name','shortname','description','parent','category',
                'level') #afrocode may be null
            }),
        )
    list_display=('name','code','shortname','parent','category','level',)
    list_select_related = ('parent',)
    list_display_links =('code', 'name','shortname',)
    search_fields = ('translations__name','translations__shortname','code',)
    exclude = ('date_created','date_lastupdated','code',)
    list_per_page = 30 #limit records displayed on admin site to 15
    list_filter = (
        ('parent',TranslatedFieldFilter),
        ('level',DropdownFilter,),# Added 16/12/2019 for M2M lookup
    )


# Register data import wizard for the custom serializer defined in wizard.py
data_wizard.register(
    "Health Facilities Import", DataWizardFacilitySerializer)

@admin.register(StgHealthFacility)
class FacilityAdmin(ImportExportModelAdmin,ImportExportActionModelAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }
    """
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).select_related('type','owner',
            'location__location','user').filter(
            location__location__translations__language_code=language).order_by(
            'location__location__translations__name').distinct()
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().select_related(
                        'parent','locationlevel','wb_income','special').order_by(
                        'location_id')
        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location<=2:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gt=2,
                locationlevel__locationlevel_id__lte=3)
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1:
            qs=qs.filter(location=user_location)
        else: # return own data if not member of a group
            qs=qs.filter(user=request.user).distinct()
        return qs

    """
    Serge requested that the form for data input be restricted to user location.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.===modified 02/02/2021
    """
    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        qs = super().get_queryset(request)
        groups = list(request.user.groups.values_list('user', flat=True))
        language = request.LANGUAGE_CODE
        user = request.user.id
        email = request.user.email
        user_location = request.user.location.location_id
        countrycodes=StgLocationCodes.objects.values_list(
            'country_code',flat=True)
        # This queryset is used to load specific phone code for logged in user
        country_code = countrycodes.filter(location=request.user.location)

        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocationCodes.objects.all().filter(
                location__translations__language_code=language).order_by(
                'location_id')

                # Looks up for the location level upto the country level
            elif user in groups and user_location==1:
                kwargs["queryset"] = StgLocationCodes.objects.filter(
                location__locationlevel__locationlevel_id__gte=1,
                location__locationlevel__locationlevel_id__lte=2).order_by(
                'location_id')
            else:
                kwargs["queryset"] = StgLocationCodes.objects.filter(
                location_id=user_location).order_by('location_id')

        if db_field.name == "phone_code":
            kwargs["queryset"]=country_code # very sgood

        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(email=email)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    """
    Returns available export formats.
    """
    def get_import_formats(self):
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]

    def get_export_formats(self):
        """
        Returns available export formats.
        """
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

    def get_export_resource_class(self):
        return StgFacilityResourceExport

    # Format date created to disply only the day, month and year
    def date_created (obj):
        return obj.date_created.strftime("%d-%b-%Y")
    date_created.admin_order_field = 'date_created'
    date_created.short_description = 'Date Created'


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
        ('Health Facility Details', {
                'fields':('name','shortname','type','description','owner',
                'location','admin_location','status') #afrocode may be null
            }),
            ('Geolocation and Contact Details', {
                'fields': ('latitude','longitude','altitude','geosource',
                'address','email','phone_code','phone_part','url',),
            }),
        )
    # To display the choice field values use the helper method get_foo_display
    list_display=('name','code','type','owner','location','admin_location',
    'latitude','longitude','geosource','status','phone_number',date_created,)
    # make a 1 query join instead of multiple individual queries
    list_select_related = ('type','owner','location__location','user',)
    list_display_links = ['code','name',]
    search_fields = ('name','type__translations__name','status','shortname',
        'code',   'code','location__location__translations__name',
        'owner__translations__name')
    list_per_page = 50 #limit records displayed on admin site to 50
    exclude = ('date_created','date_lastupdated','code',)
    readonly_fields = ('phone_code',)
    list_filter = (
        ('location',TranslatedFieldFilter),
        ('type',TranslatedFieldFilter),
        ('owner',TranslatedFieldFilter),
        ('status',DropdownFilter),
    )


@admin.register(FacilityServiceAvailabilityProxy)
class FacilityServiceAvailabilityAdmin(ExportActionModelAdmin,OverideExport):
    change_form_template = "admin/change_form_availability.html"
    def response_change(self, request, obj):
        if "_capacity-form" in request.POST:
            pass # to be omplemented later to load service capacity form
        if "_readiness-form" in request.POST:
            pass #to be omplemented later to load servicereadiness form
        return super().response_change(request, obj)

    def get_export_resource_class(self):
        return StgFacilityServiceAvailabilityExport

    # This method removes the add button on the admin interface
    """
   Serge requested that a user does not see other users or groups data.
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')

        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            return qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1:
            qs=qs.filter(location=user_location)
        else: # return own data if not member of a group
            qs=qs.filter(user=request.user).distinct()
        return qs

    """
    Serge requested that the form for data input be restricted to user's country.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.=== modified 02/02/2021
    """
    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        qs = super().get_queryset(request)
        email = request.user.email
        db_sevicedomains = StgServiceDomain.objects.all()
        db_sevicesubdomains=db_sevicedomains.exclude(
            parent_id__isnull=True).filter(category=1)

        if db_field.name == "domain":
            kwargs["queryset"]=db_sevicesubdomains

        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(email=email)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    def has_add_permission(self, request, obj=None):
        return False

    #This function limits the import format to CSV, XML and XLSX
    def get_import_formats(self):
        """
        This function returns available export formats.
        """
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]

    # This function limits the export format to CSV, XML and XLSX
    def get_export_formats(self):
        """
        This function returns available export formats.
        """
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

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
        ('Facility Details', {
                'fields':('name','type','location','admin_location','owner',)
            }),
        )

    inlines = [FacilityServiceAvailabilityInline] # Displays tabular subform
    list_display=('name','type','location','admin_location','owner',)
    list_select_related = ('type','owner','location','owner',)
    readonly_fields = ('name','type','location','admin_location','owner',)
    list_filter = (
        ('location',TranslatedFieldFilter),
        ('type',TranslatedFieldFilter),
        ('owner',TranslatedFieldFilter),
        ('status',DropdownFilter),
    )


@admin.register(FacilityServiceProvisionProxy)
class FacilityServiceProvisionAdmin(ExportActionModelAdmin,OverideExport):
    change_form_template = "admin/change_form_capacity.html"
    def response_change(self, request, obj):
        if "_capacity-availability" in request.POST:
            pass # to be omplemented later to load service capacity form
        if "_readiness-form" in request.POST:
            pass #to be omplemented later to load servicereadiness form
        return super().response_change(request, obj)

    def get_export_resource_class(self):
        return StgFacilityServiceCapacityExport

    #This method removes the add button on the admin interface
    def has_add_permission(self, request, obj=None):
        return False

    def get_import_formats(self): #This method limits import to CSV, XML and XLSX
        """
        This function returns available export formats.
        """
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]

    def get_export_formats(self): #This function returns available export formats.
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

    # This method removes the add button on the admin interface
    """
    Serge requested that a user does not see other users or groups data.This
    method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')

        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            return qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1:
            qs=qs.filter(location=user_location)
        else: # return own data if not member of a group
            qs=qs.filter(user=request.user).distinct()
        return qs

    """
    Serge requested that the form for data input be restricted to use country.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.=== modified 02/02/2021
    """
    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        qs = super().get_queryset(request)
        email = request.user.email
        db_sevicedomains = StgServiceDomain.objects.all()
        db_sevicesubdomains=db_sevicedomains.exclude(
            parent_id__isnull=True).filter(category=1)
        if db_field.name == "domain":
            kwargs["queryset"]=db_sevicesubdomains
        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(
                    email=email)
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
        ('FACILITY DETAILS', {
                'fields':('name','type','location','admin_location','owner',)
            }),
        )
    inlines = [FacilityServiceCapacityInline]
    list_display=('name','type','location','admin_location','owner',)
    list_select_related = ('type','owner','location','owner',)
    readonly_fields = ('name','type','location','admin_location','owner')
    search_fields = ('name','type__translations__name','status','shortname',
        'code',   'code','location__location__translations__name',
        'owner__translations__name')
    list_per_page = 50 #limit records displayed on admin site to 50
    list_filter = (
        ('location',TranslatedFieldFilter),
        ('type',TranslatedFieldFilter),
        ('owner',TranslatedFieldFilter),
        ('status',DropdownFilter),
    )


@admin.register(FacilityServiceReadinesProxy)
class FacilityServiceReadinessAdmin(ExportActionModelAdmin,OverideExport):
    # This method adds custom change buttons
    change_form_template = "admin/change_form_readiness.html"
    def response_change(self, request, obj):
        if "_capacity-availability" in request.POST:
            pass # to be omplemented later to load service capacity form
        if "_readiness-form" in request.POST:
            pass #to be omplemented later to load servicereadiness form
        return super().response_change(request, obj)
    # This method removes the add button on the admin interface

    def get_export_resource_class(self):
        return StgFacilityServiceReadinessExport

    """
   Serge requested that a user does not see other users or groups data.
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            return qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1:
            qs=qs.filter(location=user_location)
        else: # return own data if not member of a group
            qs=qs.filter(user=request.user).distinct()
        return qs

    """
    Serge requested that the form for data input be restricted to user's country.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.=== modified 02/02/2021
    """
    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        qs = super().get_queryset(request)
        email = request.user.email
        db_sevicedomains = StgServiceDomain.objects.all()
        db_sevicesubdomains=db_sevicedomains.exclude(
            parent_id__isnull=True).filter(category=1)

        if request.user.is_superuser:
            if db_field.name == "domain":
                kwargs["queryset"]=db_sevicesubdomains
        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(
                    email=email)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    #This method removes the add button on the admin interface
    def has_add_permission(self, request, obj=None):
        return False

    def get_import_formats(self):  #This method limits import to CSV, XML and XLSX
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]

    def get_export_formats(self): #This function returns available export formats.
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

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
        ('FACILITY DETAILS', {
                'fields':('name','type','location','admin_location','owner',)
            }),
        )
    inlines = [FacilityServiceReadinessInline]
    list_display=('name','type','location','admin_location','owner',)
    list_select_related = ('type','owner','location','owner',)
    readonly_fields = ('name','type','location','admin_location','owner',)
    search_fields = ('name','type__translations__name','status','shortname',
        'code',   'code','location__location__translations__name',
        'owner__translations__name')
    list_per_page = 50 #limit records displayed on admin site to 50
    list_filter = (
        ('location',TranslatedFieldFilter),
        ('type',TranslatedFieldFilter),
        ('owner',TranslatedFieldFilter),
        ('status',DropdownFilter),
    )


@admin.register(StgFacilityServiceMeasureUnits)
class FacilityServiceProvisionUnitsAdmin (TranslatableAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    # This method removes the add button on the admin user interface
    """
   Serge requested that a user does not see other users or groups data.
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.username
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            return qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1:
            qs=qs.filter(username=user)
        return qs
    fieldsets = (
        ('Unit of Service provision', {
                'fields':('name','shortname','description','domain',)
            }),
        )
    list_display=('name','code','shortname','domain','description')
    list_select_related = ('domain',)
    list_display_links =('code', 'name',)
    search_fields = ('code','translations__name',) #display search field
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)
    list_filter = (
        ('domain',RelatedOnlyDropdownFilter),
    )



@admin.register(StgFacilityServiceIntervention)
class FacilityServiceInterventionAdmin(TranslatableAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }
    # This method removes the add button on the admin interface
    """
   Serge requested that a user does not see other users or groups data.
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.username
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            return qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1:
            qs=qs.filter(username=user)
        return qs
    fieldsets = (
        ('Service Interventions Details', {
                'fields':('name','shortname','description','domain',)
            }),
        )
    list_display=('name','code','shortname','description','domain',)
    list_select_related = ('domain',)
    list_display_links =('code', 'name','shortname',)
    search_fields = ('translations__name','translations__shortname','code',)
    exclude = ('date_created','date_lastupdated','code',)
    list_per_page = 30 #limit records displayed on admin site to 15
    list_filter = (
        ('domain',TranslatedFieldFilter),
    )


@admin.register(StgFacilityServiceAreas)
class FacilityServiceAreasAdmin(TranslatableAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }
    # This method removes the add button on the admin interface
    """
   Serge requested that a user does not see other users or groups data.
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.username
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        # Returns data for all the locations to the lowest location level
        if request.user.is_superuser:
            return qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1:
            qs=qs.filter(username=user)
        return qs
    fieldsets = (
        ('Service Domain Areas', {
                'fields':('name','shortname','description','intervention',)
            }),
        )

    list_display=('name','code','shortname','description','intervention',)
    list_select_related = ('intervention',)
    list_display_links =('code', 'name','shortname',)
    search_fields = ('translations__name','translations__shortname','code',)
    exclude = ('date_created','date_lastupdated','code',)
    list_per_page = 30 #limit records displayed on admin site to 15
    list_filter = (
        ('intervention',TranslatedFieldFilter),
    )
