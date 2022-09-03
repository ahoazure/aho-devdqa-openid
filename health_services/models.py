from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone
import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.fields import DecimalField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields
from home.models import (StgDatasource,StgCategoryoption,StgMeasuremethod,
    StgValueDatatype,StgPeriodType)
from indicators.models import (StgIndicatorReference, StgIndicatorDomain,
    IndicatorProxy,StgIndicator,)
from regions.models import StgLocation
from authentication.models import CustomUser

# These are global codes reusable in most models that require choice fiels
def make_choices(values):
    return [(v, v) for v in values]

def current_year():
    return datetime.date.today().year

def max_value_current_year(value):
    return MaxValueValidator(current_year())(value)

STATUS_CHOICES = ( #choices for approval of indicator data by authorized users
    ('pending', _('Pending')),
    ('approved',_('Approved')),
    ('rejected',_('Rejected')),
)

class HealthServices_DataIndicators(models.Model):
  # discriminator for ownership of data this was decided on 13/12/2019 with Gift
    fact_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)') # request helper field
    indicator = models.ForeignKey(StgIndicator, models.PROTECT,
        verbose_name = _('Indicator Name'))
    location = models.ForeignKey(StgLocation, models.PROTECT,blank=False,
        verbose_name = _('Location Name'),)
    categoryoption = models.ForeignKey(StgCategoryoption, models.PROTECT,
        blank=False,verbose_name =_('Disaggregation Options'))
    # This field is used to lookup data sources e.g. routine, census and surveys
    datasource = models.ForeignKey(StgDatasource, models.PROTECT,
        verbose_name = _('Data Source'))
    # This field is used to lookup the type of data required e.g.text, integer or float
    measuremethod = models.ForeignKey(StgMeasuremethod,models.PROTECT,
        blank=False,verbose_name =_('Measure Type'))
    numerator_value = models.DecimalField(_('Numerator Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    denominator_value = models.DecimalField(_('Denominator Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    value_received = DecimalField(_('Data Value'),max_digits=20,
        decimal_places=3,blank=True,null=True,)
    value_calculated = models.DecimalField(_('Calculated Value'),max_digits=20,
        decimal_places=3,blank=True,null=True,editable=False)
    min_value = models.DecimalField(_('Minimum Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    max_value = models.DecimalField(_('Maximum Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    target_value = models.DecimalField(_('Target Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    periodicity = models.ForeignKey(StgPeriodType, models.PROTECT,
        verbose_name ='Reporting Periodicity',default=1,)  # Field name made lowercase.
    start_period = models.DateField(_('Starting Date'),null=False,blank=False,
        default=timezone.now,help_text=_("Start of reporting Period"))
    end_period=models.DateField(_('Ending Date'),null=True,blank=True,
        default=timezone.now,help_text=_("End of reporting Period"))
    period = models.CharField(_('Period'),max_length=25,blank=True,null=False)
    comment = models.CharField(_('Status'),max_length=10, choices= STATUS_CHOICES,
        default=STATUS_CHOICES[0][0])  # Field name made lowercase.
    has_lastdate = models.BooleanField(default=False,verbose_name='Show End Date?')
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        permissions = (
            ("approve_facthealthservices","Can approve Health Services Data"),
            ("reject_facthealthservices","Can reject Health Services Data"),
            ("pend_facthealthservices","Can pend Health Services Data")
        )

        managed = True
        unique_together = ('indicator', 'location', 'categoryoption','datasource',
            'start_period','end_period') #enforces concatenated unique constraint
        db_table = 'fact_health_services'
        verbose_name = _('Single Record')
        verbose_name_plural = _('    Single-Record Form')
        ordering = ('indicator__translations__name',)

    def __str__(self):
         return str(self.indicator)

    def clean(self):
        from django.core.exceptions import ValidationError
        today = datetime.date.today()
        months_delta = (self.end_period.month-self.start_period.month)+1
        # import pdb; pdb.set_trace()
        if self.end_period:
            if self.end_period > today:
                raise ValidationError("You cannot set an end date in future")
        if self.has_lastdate and self.end_period is None:
            raise ValidationError("Please provide an end date!")

        if self.periodicity.period_id==2:
            if months_delta <=1 and months_delta > 3:
                raise ValidationError("Quarter cannot be more than 3 months!")

    def get_period(self):
        if self.period is None or (self.start_period and self.end_period):
            if self.periodicity.period_id == 1:
                start = self.start_period.month
                end = self.end_period.month
                year = self.start_period.year
                if start <10:
                    period = str(year)+'-0'+str(start)
                else:
                    period = str(year)+'-'+str(start)
            elif self.periodicity.period_id == 2:
                current_quarter = round((self.start_period.month - 1) / 3 + 1)
                period = str( self.start_period.year)+'-Q'+str(current_quarter)
            elif self.periodicity.period_id == 3:
                if self.end_period.month>=1 and self.end_period.month<7:
                    period = str( self.start_period.year)+'-S1'
                else:
                    period = str( self.start_period.year)+'-S2'
            elif self.periodicity.period_id == 4:
                period= str(self.start_period.year)
            else:
                if self.start_period.year!=self.end_period.year:
                    period = str( self.start_period.year)+'-'+str(self.end_period.year)
                else:
                    period = str( self.start_period.year)
        return period


    def get_calculated_value(self):
        calculated_value =self.value_calculated
        numerator=self.numerator_value
        denom =self.denominator_value
        factor = self.measuremethod.measure_value


        if (numerator is not None or numerator !='') and \
            (denom is not None or denom !=0 or denom!=''):
            calculated_value = (numerator/denom)*factor
        else:
            calculated_value =None
        return calculated_value


    def save(self, *args, **kwargs):
        if self.value_calculated:
            self.period = self.get_period()
        if self.value_calculated:
            self.value_calculated = round(self.get_calculated_value(),3)
        super(HealthServices_DataIndicators, self).save(*args, **kwargs)



# These proxy classes are used to register menu in the admin for tabular entry
class HealthServicesIndicatorProxy(StgIndicator):
    """
    Creates permissions for proxy models which are not created automatically by
    'django.contrib.auth.management.create_permissions'.Since we can't rely on
    'get_for_model' we must fallback to  'get_by_natural_key'. However, this
    method doesn't automatically create missing 'ContentType' so we must ensure
    all the models' 'ContentType's are created before running this method.
    We do so by unregistering the 'update_contenttypes' 'post_migrate' signal
    and calling it in here just before doing everything.
    """
    def create_proxy_permissions(app, created_models, verbosity, **kwargs):
        update_contenttypes(app, created_models, verbosity, **kwargs)
        app_models = models.get_models(app)
        # The permissions we're looking for as (content_type, (codename, name))
        searched_perms = list()
        # The codenames and ctypes that should exist.
        ctypes = set()
        for model in app_models:
            opts = model._meta
            if opts.proxy:
                # Can't use 'get_for_model' here since it doesn't return correct
                # 'ContentType' for proxy models
                app_label, model = opts.app_label, opts.object_name.lower()
                ctype = ContentType.objects.get_by_natural_key(app_label, model)
                ctypes.add(ctype)
                for perm in _get_all_permissions(opts, ctype):
                    searched_perms.append((ctype, perm))

        all_perms = set(Permission.objects.filter(
            content_type__in=ctypes,
        ).values_list(
            "content_type", "codename"
        ))

        objs = [
            Permission(codename=codename, name=name, content_type=ctype)
            for ctype, (codename, name) in searched_perms
            if (ctype.pk, codename) not in all_perms
        ]
        Permission.objects.bulk_create(objs)
        if verbosity >= 2:
            for obj in objs:
                sys.stdout.write("Adding permission '%s'" % obj)
        models.signals.post_migrate.connect(create_proxy_permissions)
        models.signals.post_migrate.disconnect(update_contenttypes)

    class Meta:
        proxy = True
        managed = False
        verbose_name = 'Multi-Records Form'
        verbose_name_plural = '   Multi-Records Form'

    def clean(self): #Appreciation to Daniel M.
        pass


# These proxy classes are used to register menu in the admin for tabular entry
class HealthServicesIndicators(StgIndicator):
    def create_proxy_permissions(app, created_models, verbosity, **kwargs):
        update_contenttypes(app, created_models, verbosity, **kwargs)
        app_models = models.get_models(app)
        # The permissions we're looking for as (content_type, (codename, name))
        searched_perms = list()
        # The codenames and ctypes that should exist.
        ctypes = set()
        for model in app_models:
            opts = model._meta
            if opts.proxy:
                # Can't use 'get_for_model' here since it doesn't return correct
                # 'ContentType' for proxy models
                app_label, model = opts.app_label, opts.object_name.lower()
                ctype = ContentType.objects.get_by_natural_key(app_label, model)
                ctypes.add(ctype)
                for perm in _get_all_permissions(opts, ctype):
                    searched_perms.append((ctype, perm))

        all_perms = set(Permission.objects.filter(
            content_type__in=ctypes,
        ).values_list(
            "content_type", "codename"
        ))

        objs = [
            Permission(codename=codename, name=name, content_type=ctype)
            for ctype, (codename, name) in searched_perms
            if (ctype.pk, codename) not in all_perms
        ]
        Permission.objects.bulk_create(objs)
        if verbosity >= 2:
            for obj in objs:
                sys.stdout.write("Adding permission '%s'" % obj)
        models.signals.post_migrate.connect(create_proxy_permissions)
        models.signals.post_migrate.disconnect(update_contenttypes)

    class Meta:
        proxy = True
        managed = False
        verbose_name = 'HSC Indicator'
        verbose_name_plural = ' HSC Indicators'

    def clean(self): #Appreciation to Daniel M.
        pass



# This class similar to indicator domains is used to create HSC programmes
class HealthServicesProgrammes(TranslatableModel):
    LEVEL = (
    (1,_('level 1')),
    (2,_('level 2')),
    (3,_('level 3')),
    (4,_('level 4')),
    )
    domain_id = models.AutoField(primary_key=True)  # Field name made lowercase.
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(unique=True, max_length=45, blank=True,
        null=True,verbose_name = _('Code'))
    translations = TranslatedFields(
        name = models.CharField(_('Programme Name'),max_length=150, blank=False,
        null=False),
        shortname = models.CharField(_('Short Name'),max_length=45,blank=False,
            null=False),
        description = models.TextField(_('Description'),blank=True,null=True,)
    )
    level =models.SmallIntegerField(_('Level'),choices=LEVEL,
        default=LEVEL[0][0])
    parent = models.ForeignKey('self', models.PROTECT, blank=True, null=True,
        verbose_name = _('Main Programme'))  # Field name made lowercase.
    # this field establishes a many-to-many relationship with the domain table
    indicators = models.ManyToManyField(HealthServicesIndicators,blank=True,
        db_table='stg_health_continuity_indicators',verbose_name = _('HSC Indicators'))  # Field name made lowercase.
    date_created = models.DateTimeField(_('Date Created'),blank=True,null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_health_continuity_programs'
        verbose_name = _('HSC Programme')
        verbose_name_plural = _(' HSC Programmes')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #ddisplay disagregation options

    # The filter function need to be modified to work with django parler as follows:
    def clean(self): # Don't allow end_period to be greater than the start_period.
        if StgIndicatorDomain.objects.filter(
            translations__name=self.name).count() and not self.domain_id:
            raise ValidationError({'name':_('Sorry! This Programme already exists')})

    def save(self, *args, **kwargs):
        super(HealthServicesProgrammes, self).save(*args, **kwargs)



"""
This model class maps to a database view that looks up the django_admin logs,
location, customuser and group
"""
class HSCPrograms_Lookup(models.Model):
    indicator_id = models.AutoField(primary_key=True)
    indicator_name = models.CharField(_("HSC Indicator"),blank=False,null=False,
        max_length=500)
    code = models.CharField(_("Indicator Code"),max_length=10, blank=True)
    program_name  = models.CharField(_("HSC Programme"),max_length=230, blank=True)
    level  = models.IntegerField(_("Level"),null=False,blank=False)

    class Meta:
        managed = False
        db_table = 'vw_hsc_indicators_lookup'
        verbose_name = _('Programs Lookup')
        verbose_name_plural = _('Programs Lookup')
        ordering = ('indicator_name', )

    def __str__(self):
        return self.indicator_name
