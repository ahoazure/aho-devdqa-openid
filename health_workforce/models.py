from django.db import models
import uuid
import datetime
from django.db.models.fields import DecimalField
from django.core.validators import (RegexValidator,MinValueValidator,
    MaxValueValidator)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _ # The _ is alias for gettext
from parler.models import TranslatableModel, TranslatedFields
from publications.models import (StgResourceType,StgKnowledgeProduct,
    StgProductDomain,StgResourceCategory)
from regions.models import StgLocation
from facilities.models import (StgHealthFacility,)
from authentication.models import CustomUser
from home.models import (StgDatasource,StgCategoryoption,StgMeasuremethod)

def make_choices(values):
    return [(v, v) for v in values]

def current_year():
    return datetime.date.today().year

def max_value_current_year(value):
    return MaxValueValidator(current_year())(value)

"""
Knowledge Resource proxy model.The def clean (self) method was contributed
by Daniel Mbugua to resolve the issue of parent-child saving issue in the
multi-records entry form.My credits to Mr Mbugua of MSc DCT, UoN-Kenya

"""
class ResourceTypeProxy(StgResourceType):
    class Meta:
        proxy = True
        verbose_name = _('Resource Type')
        verbose_name_plural = _('Resource Types')

    def clean(self):
        pass


class HumanWorkforceResourceProxy(StgKnowledgeProduct):
    class Meta:
        proxy = True
        verbose_name = _('Resource/Guide')
        verbose_name_plural = _('Resources/Guides')

    def clean(self):
        pass


class ResourceCategoryProxy(StgResourceCategory):
    class Meta:
        proxy = True
        verbose_name = _('Resource Category')
        verbose_name_plural = _('Resource Categories')

    def clean(self):
        pass


# New model to take care of resource types added 11/05/2019 courtesy of Gift
class StgInstitutionType(TranslatableModel):
    FLAG = ('publications','health_workforce','general',)
    type_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(_('Code'),unique=True, max_length=50, blank=True,
        null=True)  # Field name made lowercase.
    translations = TranslatedFields(
        name = models.CharField(_('Name'),max_length=230, blank=False, null=False),
        shortname = models.CharField(_('Short Name'),max_length=230, blank=True,
            null=True),  # Field name made lowercase.
        description = models.TextField(_('Brief Description'),blank=True, null=True)
    )
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_institution_type'
        verbose_name = _('Institution Type')
        verbose_name_plural = _(' Institution Types')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the knowledge product category name


# New model to take care of resource types added 11/05/2019 courtesy of Gift
class StgInstitutionProgrammes(TranslatableModel):
    course_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(_('Code'),unique=True, max_length=50, blank=True,
        null=True)  # Field name made lowercase.
    translations = TranslatedFields(
        name = models.CharField(_('Type Name'),max_length=230, blank=False,
            null=False),  # Field name made lowercase.
        shortname = models.CharField(_('Short Name'),max_length=230, blank=True,
            null=True),  # Field name made lowercase.
        description = models.TextField(_('Brief Description'),blank=True, null=True)
    )
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_institution_programme'
        verbose_name = _('Training Programme')
        verbose_name_plural = _(' Training Programmes')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the knowledge product category name


class StgTrainingInstitution(TranslatableModel):
    STATUS_CHOICES = ( #choices for approval of indicator data by authorized users
        ('accredited', _('Accredited')),
        ('charterted',_('Chartered')),
        ('unacredited',_('Not Accredited')),
        ('pending',_('Pending Accreditation')),
    )
    phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$', message="Phone format: '+999999999' maximum 15.")
    institution_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    user = models.ForeignKey(CustomUser, models.PROTECT,blank=True,
		verbose_name = 'User Name (Email)',) ## request helper field
    code = models.CharField(unique=True, max_length=15, blank=True, null=False,
        verbose_name = _('Institution Code'))  # Field name made lowercase.
    location = models.ForeignKey(StgLocation, models.PROTECT,blank=True,
        null=False, verbose_name = _('Location'),)
    type = models.ForeignKey(StgInstitutionType, models.PROTECT, blank=False,
        null=False, verbose_name = _('Institution Type'),default=6)
    programmes = models.ManyToManyField(StgInstitutionProgrammes,
        db_table='stg_institution_programs_lookup',blank=True,
        verbose_name = _('Training Programmes'))
    translations = TranslatedFields(
        name = models.CharField(_('Institution Name'),max_length=230,blank=False,
            null=False),  # Field name made lowercase.
        faculty =models.CharField(_('Faculty Name'),max_length=150,
            blank=True,null=True),  # Field name made lowercase.
        accreditation = models.CharField(_('Accreditation Status'),max_length=50,
            choices= STATUS_CHOICES,default=STATUS_CHOICES[0][0]),
        regulator = models.CharField(_('Regulatory Body'),max_length=150,
            blank=True,null=True),
        accreditation_info = models.CharField(_('Accreditation Details'),
            max_length=2000, blank=True),
        language = models.CharField(_('Teaching Language'),max_length=50,
            blank=True,null=True),
        address = models.CharField(_('Contact Person'),max_length=500,
            blank=True,null=True),
        posta = models.CharField(_('Post Address'),max_length=500,blank=True,
            null=True),
        email = models.EmailField(_('Email'),unique=True,max_length=150,blank=True,
            null=True),  # Field name made lowercase.
        phone_number = models.CharField(_('Phone Number'),
            validators=[phone_regex], max_length=15, blank=True),#validators list
        url = models.URLField(_('Web Address'),blank=True, null=True,
            max_length=2083),
        latitude = models.FloatField(_('Latitude'),blank=True, null=True),
        longitude = models.FloatField(_('Longitude'),blank=True, null=True),
    )
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_traininginstitution'
        verbose_name = _('Institution')
        verbose_name_plural = _('  Training Institutions')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the location name such as country

    """
    This function makes sure the location name is unique instead of enforcing
    unque constraint on DB
    """
    def clean(self): # Don't allow end_year to be greater than the start_year.
        if StgTrainingInstitution.objects.filter(
            translations__name=self.name).count() and not self.institution_id:
            raise ValidationError(
                {'name':_('Training Institution with the this name exists')})

    def save(self, *args, **kwargs):
        super(StgTrainingInstitution, self).save(*args, **kwargs)


class StgHealthCadre(TranslatableModel):
    STATUS_CHOICES = ( #choices for approval of indicator data by authorized users
        ('degree', _('Degree')),
        ('diploma', _('Diploma')),
        ('masters',_('Masters')),
        ('phd',_('Doctorate')),
        ('certificate',_('Certificate')),
        ('basic',_('Basic Education')),

    )
    cadre_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False, default=uuid.uuid4,editable=False)
    code = models.CharField(unique=True, blank=True,null=False,
        max_length=45,verbose_name=_('ISCO-08 Code'))
    parent = models.ForeignKey('self', models.PROTECT,blank=True, null=True,
        verbose_name = _('Parent Cadre'),default=1,)
    translations = TranslatedFields(
        name = models.CharField(_('Cadre Name'),max_length=230,blank=False,
            null=False),  # Field name made lowercase.
        shortname = models.CharField(_('Short Name'),max_length=230,blank=False,
            null=False),  # Field name made lowercase.
        academic = models.CharField(_('Academic Qualification'),max_length=15,
            choices= STATUS_CHOICES,default=STATUS_CHOICES[0][0]),
        description = models.TextField(_('Brief Description'),blank=True, null=True)
    )  # End of translatable fields
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_health_cadre'
        verbose_name = _('Health Cadre')
        verbose_name_plural = _('   Health Cadres')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the data element name

    def clean(self): # Don't allow end_year to be greater than the start_year.
        import datetime
        if StgHealthCadre.objects.filter(
            translations__name=self.name).count() and not self.code:
            raise ValidationError({'name':_('The same occupation/cadre exists')})

    def save(self, *args, **kwargs):
        super(StgHealthCadre, self).save(*args, **kwargs)


class StgHealthWorkforceFacts(models.Model):
    STATUS_CHOICES = ( #choices for approval of indicator data by authorized users
        ('pending', _('Pending')),
        ('approved',_('Approved')),
        ('rejected',_('Rejected')),
    )
    AGGREGATION_TYPE = ('Count','Sum','Average','Standard Deviation',
        'Variance', 'Min', 'max','None')
    fact_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False, default=uuid.uuid4,editable=False)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
		verbose_name = 'User Name (Email)',) ## request helper field
    cadre = models.ForeignKey(StgHealthCadre, models.PROTECT,
        verbose_name = _('Occupation/Cadre'),default = 1)  # disallow deletion
    location = models.ForeignKey(StgLocation, models.PROTECT,
        verbose_name = _('Location'),)
    categoryoption = models.ForeignKey(StgCategoryoption, models.PROTECT,
        verbose_name = _('Disaggregation Options'))  # disallow deletion
    datasource = models.ForeignKey(StgDatasource, models.PROTECT,blank=False,
        null=False,verbose_name = _('Data Source'), default = 1)
    measuremethod = models.ForeignKey(StgMeasuremethod, models.PROTECT,blank=True,
        null=True, verbose_name = _('Measure Type'))  # Field name made lowercase.
    value = DecimalField(_('Data Value'),max_digits=20,decimal_places=3,
        blank=False, null=False)  # Field name made lowercase.
    start_year = models.PositiveIntegerField(_('Starting period'),null=False,
        blank=False,validators=[MinValueValidator(1900),max_value_current_year],
        default=current_year(),
        help_text=_("This marks the start of reporting period"))
    end_year  = models.PositiveIntegerField(_('Ending Period'),null=False,
        blank=False,validators=[MinValueValidator(1900)],default=current_year(),
        help_text=_("This marks the end of reporting. The value must be current \
            year or greater than the start year"))
    period = models.CharField(_('Period'),max_length=10,blank=True,
        null=False) #try to concatenate period field
    status = models.CharField(_('Status'),max_length=10, choices= STATUS_CHOICES,
        default=STATUS_CHOICES[0][0])
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        permissions = ( # This permissions were missing --- added 0n 28/09/2021
            ("approve_stghealthworkforcefacts","Can approve Workforce Data"),
            ("pend_stghealthworkforcefacts","Can reject Workforce Data"),
            ("reject_stghealthworkforcefacts","Can pend Workforce Data")
        )

        managed = True
        unique_together = ('cadre', 'location', 'categoryoption','datasource',
            'start_year','end_year') #enforces concatenated unique constraint
        db_table = 'fact_health_workforce'
        verbose_name = _('Health Workforce')
        verbose_name_plural = _('    Health Workforce')
        ordering = ('cadre', )

    def __str__(self):
         return str(self.cadre)
    """
    The purpose of this method is to compare the start_year to the end_year. If the
    start_year is greater than the end_year athe model should show an inlines error
    message and wait until the user corrects the mistake.
    """
    def clean(self): # Don't allow end_year to be greater than the start_year.
        if self.start_year<=1900 or self.start_year > datetime.date.today().year:
            raise ValidationError({'start_year':_(
                'Sorry! Start year cannot be less than 1900 or greater than current Year ')})
        elif self.end_year <=1900 or self.end_year > datetime.date.today().year:
            raise ValidationError({'end_year':_(
                'Sorry! The ending year cannot be lower than the start year or \
                greater than the current Year ')})
        elif self.end_year < self.start_year and self.start_year is not None:
            raise ValidationError({'end_year':_(
                'Sorry! Ending period cannot be lower than the start period. \
                 Please make corrections')})

    """
    The purpose of this method is to concatenate the date that are entered as
    start_year and end_year and save the concatenated value as a string in
    the database ---this is very important to take care of Davy's date complexity
    """
    def get_period(self):
        if self.period is None or (self.start_year and self.end_year):
            if self.start_year == self.end_year:
                period = int(self.start_year)
            else:
                period =str(int(self.start_year))+"-"+ str(int(self.end_year))
        return period

    def save(self, *args, **kwargs):
        self.period = self.get_period()
        super(StgHealthWorkforceFacts, self).save(*args, **kwargs)

class StgRecurringEvent(TranslatableModel):
    STATUS_CHOICES = ( #choices for approval of indicator data by authorized users
        ('active', _('Open')),
        ('inactive',_('Closed')),
        ('suspended',_('Suspended')),
    )
    event_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False, default=uuid.uuid4,editable=False)
    code = models.CharField(_('Event Code'),unique=True, blank=True,null=False,
        max_length=45)
    cadre = models.ManyToManyField(StgHealthCadre,
        db_table='stg_recurring_event_lookup',blank=True,
        verbose_name = _('Target Focus'))
    location = models.ForeignKey(StgLocation, models.PROTECT,
        verbose_name = _('Event Location'),default = 1)
    translations = TranslatedFields(
        name = models.CharField(_('Name of Event'),max_length=230,blank=False,
            null=False,default=_('International Year of the Nurse and the Midwife')),
        shortname = models.CharField(_('Short Name'),max_length=230,blank=False,
            null=False),  # Field name made lowercase.
        theme = models.TextField(_('Theme'),blank=True, null=True)
    )  # End of translatable fields
    internal_url = models.FileField (_('Upload File/Video(s)'),
        upload_to='media/files/events',blank=True,)  # For uploading the resource
    external_url = models.CharField(_('Web Address (URL)'), blank=True, null=True,
        max_length=2083)
    cover_image = models.ImageField(_('Upload Picture/Banner(s)'),
        upload_to='media/images/events',blank=True,) #for thumbnail..requires pillow
    start_year = models.PositiveIntegerField(_('Starting period'),null=False,
        blank=False,validators=[MinValueValidator(1900),max_value_current_year],
        default=current_year(),
        help_text=_("This marks the start of reporting period"))
    end_year  = models.PositiveIntegerField(_('Ending Period'),null=False,
        blank=False,validators=[MinValueValidator(1900)],default=current_year(),
        help_text=_("This marks the end of reporting. The value must be current \
            year or greater than the start year"))
    period = models.CharField(_('Period'),max_length=10,blank=True,
        null=False) #try to concatenate period field
    status = models.CharField(_('Status'),max_length=10, choices= STATUS_CHOICES,
        default=STATUS_CHOICES[0][0])
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_recurring_event'
        verbose_name = _('Nursing & Midwifery')
        verbose_name_plural = _('Nursing and Midwifery')
        unique_together = ('location','start_year','end_year')
        ordering = ('translations__name',)

    def __str__(self):
         return str(self.name)
    """
    The purpose of this method is to compare the start_year to the end_year. If the
    start_year is greater than the end_year athe model should show an inlines error
    message and wait until the user corrects the mistake.
    """
    def clean(self): # Don't allow end_year to be greater than the start_year.
        if self.start_year < datetime.date.today().year:
            raise ValidationError({'start_year':_(
                'Sorry! The start period year must be current or in future')})
        elif self.end_year < datetime.date.today().year:
            raise ValidationError({'end_year':_(
                'Sorry! The start period year must be current or in future')})
        elif self.end_year < self.start_year and self.start_year is not None:
            raise ValidationError({'end_year':_(
                'Sorry! End period cannot be lower than start period!')})

    """
    The purpose of this method is to concatenate dates that  entered as
    start_year and end_year and save the concatenated string in the databasey
    """
    def get_period(self):
        if self.period is None or (self.start_year and self.end_year):
            if self.start_year == self.end_year:
                period = int(self.start_year)
            else:
                period =str(int(self.start_year))+"-"+ str(int(self.end_year))
        return period

    def save(self, *args, **kwargs):
        self.period = self.get_period()
        super(StgRecurringEvent,self).save(*args, **kwargs)




class StgAnnouncements(TranslatableModel):
    STATUS_CHOICES = ( #choices for approval of indicator data by authorized users
        ('active', _('Open')),
        ('inactive',_('Closed')),
        ('suspended',_('Suspended')),
    )
    event_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False, default=uuid.uuid4,editable=False)
    code = models.CharField(_('Code'),unique=True, blank=True,
        null=False,max_length=45)
    location = models.ForeignKey(StgLocation, models.PROTECT,
        verbose_name = _('Location'),default = 1)
    translations = TranslatedFields(
        name = models.CharField(_('Announcment Title'),max_length=230,blank=False,
            null=False,),  # Field name made lowercase.
        shortname = models.CharField(_('Short Title'),max_length=230,blank=False,
            null=False,),  # Field name made lowercase.
        message = models.TextField(_('Message'),blank=True, null=True)
    )  # End of translatable fields
    internal_url = models.FileField (_('Upload File/Video(s)'),
        upload_to='media/files/events',blank=True,)  # For uploading the resource
    external_url = models.CharField(_('Web Link (URL)'), blank=True, null=True,
        max_length=2083)
    cover_image = models.ImageField(_('Upload Picture/Banner(s)'),
        upload_to='media/images/events',blank=True,) #for thumbnail..requires pillow
    start_year = models.PositiveIntegerField(_('Starting period'),null=False,
        blank=False,validators=[MinValueValidator(1900),max_value_current_year],
        default=current_year(),
        help_text=_("This marks the start of reporting period"))
    end_year  = models.PositiveIntegerField(_('Ending Period'),null=False,
        blank=False,validators=[MinValueValidator(1900),max_value_current_year],
        default=current_year(),
        help_text=_("This marks the end of reporting. The value must be current \
            year or greater than the start year"))
    period = models.CharField(_('Period'),max_length=10,blank=True,
        null=False) #try to concatenate period field
    status = models.CharField(_('Status'),max_length=10, choices= STATUS_CHOICES,
        default=STATUS_CHOICES[0][0])
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_event_announcement'
        verbose_name = _('Announcement')
        verbose_name_plural = _('Announcements')
        unique_together = ('location','start_year','end_year')
        ordering = ('translations__name',)

    def __str__(self):
         return str(self.name)
    """
    The purpose of this method is to compare the start_year to the end_year. If the
    start_year is greater than the end_year athe model should show an inlines error
    message and wait until the user corrects the mistake.
    """
    def clean(self): # Don't allow end_year to be greater than the start_year.
        if self.start_year < datetime.date.today().year:
            raise ValidationError({'start_year':_(
                'Sorry! The start period year must be current or in future')})
        elif self.end_year < datetime.date.today().year:
            raise ValidationError({'end_year':_(
                'Sorry! The start period year must be current or in future')})
        elif self.end_year < self.start_year and self.start_year is not None:
            raise ValidationError({'end_year':_(
                'Sorry! End period cannot be lower than start period!')})

    """
    The purpose of this method is to concatenate dates that  entered as start
    and end_year and save the concatenated string in the database
    """
    def get_period(self):
        if self.period is None or (self.start_year and self.end_year):
            if self.start_year == self.end_year:
                period = int(self.start_year)
            else:
                period =str(int(self.start_year))+"-"+ str(int(self.end_year))
        return period

    def save(self, *args, **kwargs):
        self.period = self.get_period()
        super(StgAnnouncements,self).save(*args, **kwargs)
