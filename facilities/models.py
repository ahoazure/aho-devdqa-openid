from django.db import models
import uuid
import datetime
# from datetime import datetime #for handling year part of date filed
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import (RegexValidator,MinValueValidator,
    MaxValueValidator)
from django.utils.translation import gettext_lazy as _ # The _ is alias for gettext
from parler.models import TranslatableModel,TranslatedFields
from regions.models import StgLocation,StgLocationCodes
from authentication.models import CustomUser # for filtering logged in instances
from smart_selects.db_fields import ChainedForeignKey # supports A->-B->C lookup

def make_choices(values):
    return [(v, v) for v in values]

# New model to take care of resource types added 11/05/2019 courtesy of Gift
class StgFacilityType(TranslatableModel):
    type_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(_('Facility Code'),unique=True, max_length=50,
        blank=True,null=True)  # Field name made lowercase.
    translations = TranslatedFields(
        name = models.CharField(_('Facility Type'),max_length=230, blank=False,
            null=False,
            ),  # Field name made lowercase.
        shortname = models.CharField(_('Short Name'),unique=True,max_length=50,
            blank=False,null=False),  # Field name made lowercase.
        description = models.TextField(_('Brief Description'),blank=True,null=True)
    )
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_facility_type'
        verbose_name = _('Facility Type')
        verbose_name_plural = _(' Facility Types')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the knowledge product category name

    def clean(self):
        if StgFacilityType.objects.filter(
            translations__name=self.name).count() and not self.type_id and not \
                self.code:
            raise ValidationError({'name':_('Facility type with the same \
                name exists')})

    def save(self, *args, **kwargs):
        super(StgFacilityType, self).save(*args, **kwargs)


class StgFacilityOwnership(TranslatableModel):
    owner_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(_('Code'),unique=True, max_length=50, blank=True,
        null=True)
    user = models.ForeignKey(CustomUser, models.PROTECT,blank=False,
		verbose_name = 'Admin User (Email)',default=2) ## request helper field
    location = models.ForeignKey(StgLocationCodes, models.PROTECT,
        verbose_name = _('Owner Country'),)
    translations = TranslatedFields(
        name = models.CharField(_('Facility Owner'),max_length=230, blank=False,
            null=False),
        shortname = models.CharField(_('Short Name'),unique=True,max_length=50,
            blank=False,null=False),  # Field name made lowercase.
        description = models.TextField(_('Description'),blank=True, null=True)
    )
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_facility_owner'
        verbose_name = _('Facility Owner')
        verbose_name_plural = _(' Facility Ownerhip')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the knowledge product category name

    def clean(self):
        if StgFacilityOwnership.objects.filter(
            translations__name=self.name).count() and not self.owner_id and not \
                self.code:
            raise ValidationError({'name':_('facility owner with the same \
                name exists')})

    def save(self, *args, **kwargs):
        super(StgFacilityOwnership, self).save(*args, **kwargs)


class StgServiceDomain(TranslatableModel):
    LEVEL = ('Level 0','Level 1','Level 2','Level 3',)

    CATEGORY = (
    (1,_('Availability')),
    (2,_('Capacity')),
    (3,_('Readiness')),
    )
    domain_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(_('Code'),unique=True, max_length=50, blank=True,
            null=True)  # Field name made lowercase.
    category = models.SmallIntegerField(_('Service Category'),choices=(CATEGORY),
        blank=False,null=False)
    level = models.CharField(_('Category Level'),max_length=50,
        choices=make_choices(LEVEL),default=LEVEL[0])
    parent = models.ForeignKey('self',on_delete=models.CASCADE,
        blank=True,null=True,verbose_name =_('Parent Domain'),)
    translations = TranslatedFields(
        name = models.CharField(_('Service Name'),max_length=230, blank=False,
            null=False),  # Field name made lowercase.
        shortname = models.CharField(_('Short Name'),max_length=45,null=True),
        description = models.TextField(_('Service Description'),blank=True,null=True)
    )
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True # must be true to create the model table in mysql
        db_table = 'stg_facility_services'
        verbose_name = _('Service Domain')
        verbose_name_plural = _(' Service Domains')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the knowledge product category name

    def clean(self):
        if StgServiceDomain.objects.filter(
            translations__name=self.name).count() and not self.domain_id and not \
                self.code:
            raise ValidationError({'name':_('Domain with the same name exists')})

    def save(self, *args, **kwargs):
        super(StgServiceDomain, self).save(*args, **kwargs)


class StgHealthFacility(models.Model):
    STATUS_CHOICES = (
        ('active', _('Active')),
        ('closed', _('Closed')),
    )
    number_regex = RegexValidator(
        regex=r'^[0-9]{8,15}$', message="Format:'999999999' min 8, maximum 15.")
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', message="Please use correct phone number format")
    latitude_regex = RegexValidator(
        regex=r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)$', message="Enter valid Latitude")
    longitude_regex = RegexValidator(
        regex=r'^[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$',
        message="Enter valid Longitude")
    facility_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(unique=True, blank=True,null=False,max_length=45)
    user = models.ForeignKey(CustomUser, models.PROTECT,blank=True,
		verbose_name = 'Admin User (Email)',) ## request helper field
    type = models.ForeignKey(StgFacilityType, models.PROTECT,blank=False,
        null=False,verbose_name = _('Facility Type'))
    location = models.ForeignKey(StgLocationCodes, models.PROTECT,
        verbose_name = _('Facility Country'),)
    owner = models.ForeignKey(StgFacilityOwnership, models.PROTECT,
        verbose_name = _('Facility Ownership'))
    name = models.CharField(_('Facility Name'),max_length=230,blank=False,
        null=False)  # Field name made lowercase.
    shortname = models.CharField(_('Short Name (Abbreviation)'),max_length=230,
        blank=True, null=True,)
    # convert this to look up to the location and then queryset lower level
    admin_location = models.CharField(_('Administrative Location'),max_length=230,
        blank=True,null=True)
    # admin_location = models.ForeignKey(StgLocation, models.PROTECT,
    #     verbose_name=_('Administrative Location'),related_name='admin_location')
    description = models.TextField(_('Description'),blank=True,
        null=True)
    address = models.CharField(_('Contact Address'),max_length=500,blank=True,
        null=True)  # Field name made lowercase.
    email = models.EmailField(_('Email'),unique=True,max_length=250,
        blank=True,null=True)  # Field name made lowercase.
    phone_code = models.CharField(_('Phone Code'), max_length=5, blank=True,
        help_text=_("Specific country code for the phone number such as +242 is \
        automatically retrieved from database of AFRO member countries"))
    phone_part = models.CharField(_('Phone Number'),validators=[number_regex],
        max_length=15, blank=True) # validators should be a list
    phone_number = models.CharField(_('Telephone'),validators=[phone_regex],
        max_length=15, null=True,blank=True) # validators should be a list
    latitude = models.DecimalField(_('Latitude'),blank=True, null=True,
        max_digits=15,decimal_places=12,)
    longitude = models.DecimalField(_('Longitude'),blank=True, null=True,
        max_digits=15,decimal_places=12,)
    altitude = models.FloatField(_('Altitude (M)'),blank=True, null=True)
    geosource = models.CharField(_('Geo-source (LL source)'),max_length=500,
        blank=True,null=True)  # Field name made lowercase.
    url = models.URLField(_('Web (URL)'),blank=True, null=True,max_length=2083)
    status = models.CharField(_('Status'),max_length=10, choices= STATUS_CHOICES,
        default=STATUS_CHOICES[0][0])
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_health_facility'
        unique_together = ('type', 'location', 'owner','name',)
        verbose_name = _('Health Facility')
        verbose_name_plural = _('    Health Facilities')
        ordering = ('name',)

    def __str__(self):
        return self.name #display the data element name

    """
    The purpose of this method is to concatenate country code and phone number
    into phone_number to be stored in ISO format---takes care of Hillary request
    """
    def get_phone(self):
        # Assign pone code to a field in related model using dot operator 4/3/2021
        self.phone_code = self.location.country_code
        phone_number = self.phone_number
        if self.phone_part is not None or self.phone_part!='':
            phone_number=(self.phone_code+self.phone_part)
        else:
            phone_number=None
        return phone_number

    """
    The purpose of this method is to populate the facility description with
    description from the related facility types model
    """
    def get_description(self):
        # Assign description to a field in related model using dot operator 6/3/2021
        description = self.type.description
        if self.description is None or self.description=='':
            description = self.name+description
        return description

    # import pdb; pdb.set_trace()

    def clean(self): # Don't allow end_period to be greater than the start_period.
        if StgHealthFacility.objects.filter(name=self.name).count() and not \
            self.facility_id and not self.type and not self.location:
            raise ValidationError({'name':_('Facility  with the same name exists')})

    def save(self, *args, **kwargs):
        self.phone_number = self.get_phone()
        self.description  = self.get_description()
        super(StgHealthFacility, self).save(*args, **kwargs)


# Model to take care of units of provision for service capacity and readiness
class StgFacilityServiceMeasureUnits(TranslatableModel):
    infra_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(_('Code'),unique=True, max_length=50,
        blank=True,null=True)
    domain = models.ForeignKey(StgServiceDomain, models.PROTECT,blank=False,
        null=False,verbose_name=_('Service Provision Category'))
    translations = TranslatedFields(
        name = models.CharField(_('Units of Provision'),max_length=230,
            blank=False, null=False),  # Field name made lowercase.
        shortname = models.CharField(_('Short Name'),unique=True,max_length=50,
            blank=True,null=True),  # Field name made lowercase.
        description = models.TextField(_('Description'),blank=True, null=True)
    )
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_facility_service_units'
        verbose_name = _('Provision Unit')
        verbose_name_plural = _('Provision Units')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the knowledge product category name

    def clean(self):
        if StgFacilityServiceMeasureUnits.objects.filter(
            translations__name=self.name).count() and not self.infra_id and not \
                self.code:
            raise ValidationError({'name':_('Unit of provision with the same \
                name exists')})

    def save(self, *args, **kwargs):
        super(StgFacilityServiceMeasureUnits, self).save(*args, **kwargs)


# New model to take care of service availability interventions
class StgFacilityServiceIntervention(TranslatableModel):
    intervention_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(_('Intervention Code'),unique=True, max_length=50,
        blank=True,null=True)
    domain = models.ForeignKey(StgServiceDomain, models.PROTECT,blank=False,
        null=False,verbose_name=_('Service Domain'))
    translations = TranslatedFields(
        name = models.CharField(_('Intervention Name'),max_length=230, blank=False,
            null=False,
            ),  # Field name made lowercase.
        shortname = models.CharField(_('Short Name'),unique=True,max_length=50,
            blank=False,null=False),  # Field name made lowercase.
        description = models.TextField(_('Description'),blank=True, null=True)  # Field name made lowercase.
    )
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_facility_service_intervention'
        verbose_name = _('Facility Servce Intervention')
        verbose_name_plural = _(' Service Interventions')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the data element name


# # New model to take care of service availability areas
class StgFacilityServiceAreas(TranslatableModel):
    area_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(_('Code'),unique=True, max_length=50,
        blank=True,null=True)
    intervention = models.ForeignKey(StgFacilityServiceIntervention,models.PROTECT,
        blank=False,null=False,verbose_name=_('Intervention Areas'),default=2)
    translations = TranslatedFields(
        name = models.CharField(_('Provision Area'),max_length=230, blank=False,
            null=False,
            ),  # Field name made lowercase.
        shortname = models.CharField(_('Short Name'),unique=True,max_length=50,
            blank=False,null=False),  # Field name made lowercase.
        description = models.TextField(_('Description'),blank=True, null=True)
    )
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_facility_service_area'
        verbose_name = _('Service Area')
        verbose_name_plural = _(' Service Areas')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the data element name


class FacilityServiceAvailability(models.Model):
    availability_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(unique=True, blank=True,null=False,max_length=50)
    user = models.ForeignKey(CustomUser, models.PROTECT,blank=False,
		verbose_name = _('Admin User (Email)'),default=2) ## request helper field
    facility = models.ForeignKey(StgHealthFacility, models.PROTECT,
        verbose_name = _('Facility Name'))
    domain = models.ForeignKey(StgServiceDomain,models.PROTECT,
        verbose_name = _('Service Area Domain'),default=2)
    intervention = ChainedForeignKey(StgFacilityServiceIntervention,
        chained_field="domain",chained_model_field="domain",show_all=False,
        auto_choose=True,on_delete=models.PROTECT,sort=True,blank=False,
        null=False,verbose_name=_('Intervention Areas'),default=1)
    service = ChainedForeignKey(StgFacilityServiceAreas,
        chained_field="intervention",chained_model_field="intervention",
        show_all=False,auto_choose=True,sort=True,on_delete=models.PROTECT,
        blank=False,null=False,verbose_name=_('Service provision Areas'),default=1)
    provided = models.BooleanField(_('Service Provided last 3 Months?'),
        default=False)
    specialunit = models.BooleanField(_('Specialized Unit Provided?'),
        default=False)
    staff = models.BooleanField(_('Staff Capacity Appropriate?'),
        default=False)
    infrastructure = models.BooleanField(_('Infrastructure Capacity Appropriate?'),
        default=False)
    supplies = models.BooleanField(_('Supplies Appropriate?'),
        default=False)
    date_assessed = models.DateField(_('Assessment Date'),null=False,blank=False,
        default=timezone.now,#extract current date year value only
        help_text=_("This marks the start of reporting period"))
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True # must be true to create the model table in mysql
        unique_together = ('domain','facility','intervention','service',
        'date_assessed',)
        db_table = 'stg_facility_services_availability'
        verbose_name = _('Service Availability')
        verbose_name_plural = _('   Services Avilability')
        ordering = ('domain',)

    def __str__(self):
        return str(self.domain)

    def save(self, *args, **kwargs):
        super(FacilityServiceAvailability,self).save(*args, **kwargs)


class FacilityServiceProvision(models.Model):
    capacity_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(unique=True, blank=True,null=False,max_length=45)
    user = models.ForeignKey(CustomUser, models.PROTECT,blank=False,
		verbose_name = 'Admin User (Email)',default=2) ## request helper field
    facility = models.ForeignKey(StgHealthFacility, models.PROTECT,
        verbose_name = _('Facility Name'))
    domain = models.ForeignKey(StgServiceDomain, models.PROTECT,blank=False,
        null=False,verbose_name = _('Service Capacity Domain'),default=2)
    units = ChainedForeignKey(StgFacilityServiceMeasureUnits,
        chained_field="domain",chained_model_field="domain",show_all=False,
        auto_choose=True,on_delete=models.PROTECT,sort=True,blank=False,
        null=False,verbose_name=_('Units of Provision'),default=1)
    available = models.PositiveIntegerField(_('Number available'),blank=False,
        null=False,help_text=_("The input must be a zero or positive integer"))
    functional = models.PositiveIntegerField(_('Number Functional'),blank=False,
        null=False,help_text=_("Functional units used in the last month"))
    date_assessed = models.DateField(_('Assessment Date'),null=False,blank=False,
        default=timezone.now,#extract current date year value only
        help_text=_("This marks the start of reporting period"))
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True # must be true to create the model table in mysql
        unique_together = ('domain','facility','units','date_assessed',)
        db_table = 'stg_facility_services_provision'
        verbose_name = _('Provision Capacity')
        verbose_name_plural = _('   Provision Capacities')
        ordering = ('domain',)

    def __str__(self):
        return str(self.domain)

    def save(self, *args, **kwargs):
        # self.period = self.get_period()
        super(FacilityServiceProvision,self).save(*args, **kwargs)


class FacilityServiceReadiness(models.Model):
    readiness_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(unique=True, blank=True,null=False,max_length=45)
    user = models.ForeignKey(CustomUser, models.PROTECT,blank=False,
		verbose_name = 'Admin User (Email)',default=2) ## request helper field
    facility = models.ForeignKey(StgHealthFacility, models.PROTECT,
        verbose_name = _('Facility Name'))
    domain = models.ForeignKey(StgServiceDomain, models.PROTECT,blank=False,
        null=False,verbose_name = _('Service Readiness Domain'),default=2)
    units = ChainedForeignKey(StgFacilityServiceMeasureUnits,
        chained_field="domain",chained_model_field="domain",show_all=False,
        auto_choose=True,on_delete=models.PROTECT,sort=True,blank=False,
        null=False,verbose_name=_('Units of Provision'),default=1)
    available = models.PositiveIntegerField(_('Number available'),blank=False,
        null=False,help_text=_("The input must be a zero or positive integer"))
    require = models.PositiveIntegerField(_('Number needed'),blank=False,
        null=False,help_text=_("Number of units needed for adequacy"))
    date_assessed = models.DateField(_('Assessment Date'),null=False,blank=False,
        default=timezone.now,#extract current date year value only
        help_text=_("This marks the start of reporting period"))
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True # must be true to create the model table in mysql
        # unique_together = ('domain','facility','start_period','end_period',
        #     'intervention')
        db_table = 'stg_facility_services_readiness'
        verbose_name = _('Service Readiness')
        verbose_name_plural = _('   Service Readiness')
        ordering = ('domain',)

    def __str__(self):
        return str(self.domain)

    def save(self, *args, **kwargs):
        # self.period = self.get_period()
        super(FacilityServiceReadiness,self).save(*args, **kwargs)


class FacilityServiceAvailabilityProxy(StgHealthFacility):
    class Meta:
        proxy = True
        managed = False
        verbose_name = 'Service Availability'
        verbose_name_plural = '  Service Availability'

    """
    This def clean (self) method was contributed by Daniel Mbugua to resolve
    the issue of parent-child saving issue in the multi-records entry form.
    My credits to Mr Mbugua of MSc DCT, UoN-Kenya
    """
    def clean(self): #Appreciation to Daniel M.
        pass

class FacilityServiceProvisionProxy(StgHealthFacility):
    class Meta:
        proxy = True
        managed = False
        verbose_name = 'Service Capacity'
        verbose_name_plural = '  Service Capacity'

    """
    This def clean (self) method was contributed by Daniel Mbugua to resolve
    the issue of parent-child saving issue in the multi-records entry form.
    My credits to Mr Mbugua of MSc DCT, UoN-Kenya
    """
    def clean(self): #Appreciation to Daniel M.
        pass


class FacilityServiceReadinesProxy(StgHealthFacility):
    class Meta:
        proxy = True
        managed = False
        verbose_name = 'Service Readiness'
        verbose_name_plural = '  Service Readiness'

    """
    This def clean (self) method was contributed by Daniel Mbugua to resolve
    the issue of parent-child saving issue in the multi-records entry form.
    My credits to Mr Mbugua of MSc DCT, UoN-Kenya
    """
    def clean(self): #Appreciation to Daniel M.
        pass
