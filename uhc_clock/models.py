from django.db import models
import uuid
import datetime
# from datetime import datetime #for handling year part of date filed
from django.utils import timezone
from django.conf import settings # allow import of language settings

from django.utils import translation as language_translations

from django.core.exceptions import ValidationError
from django.db.models.fields import DecimalField

from django.utils.translation import gettext_lazy as _ # The _ is alias for gettext
from parler.models import TranslatableModel,TranslatedFields

from indicators.models import StgIndicator
from regions.models import StgLocation # import for indicator selection

from smart_selects.db_fields import ChainedManyToManyField


"""
Returns translations language code from the login session. The language_code  
is then used in models that implement smart select to filter dropdown lists 
"""
def get_language_translations():
    language = language_translations.get_language() # get languagee 
    return language


class StgUHClockIndicatorsGroup(TranslatableModel):
    group_id = models.AutoField(primary_key=True)
    uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    translations = TranslatedFields(
        name = models.CharField(_("Reference Name"),max_length=230, blank=False,
            null=False,default=_("Day [Health Impact and Outcome]")),
        shortname = models.CharField(_('Short Name'),max_length=50,
            blank=True, null=True),
        description = models.TextField(_('Brief Description'),blank=True,null=True)
    )
    code = models.CharField(unique=True, max_length=50, blank=True,null=True)
    date_created = models.DateTimeField(_('Date Created'),blank=True,null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True,auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_uhclock_indicator_groups'
        verbose_name = _('UHC Clock Indicator Group')
        verbose_name_plural = _('  UHC Clock Indicator Groups')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the data source name

    # The filter function need to be modified to work with django parler as follows:
    def clean(self): # Don't allow end_period to be greater than the start_period.
        if StgUHClockIndicatorsGroup.objects.filter(
            translations__name=self.name).count() and not self.reference_id:
            raise ValidationError({'name':_('Sorry! This indicator reference exists')})

    def save(self, *args, **kwargs):
        super(StgUHClockIndicatorsGroup, self).save(*args, **kwargs)


class StgUHClockIndicators(models.Model):
    CATEGORIES = (
        ('1',_('Input')),
        ('2',_('Process')),      
        ('3',_('Output')),
        ('4',_('Outcomes')),
        ('5',_('Impact')),
    )
    indicator = models.OneToOneField(StgIndicator, models.PROTECT, 
        blank=False, null=False,verbose_name = _('Indicator Name'))
    group = models.ForeignKey(StgUHClockIndicatorsGroup, models.PROTECT, 
        blank=False, null=False,verbose_name = _('Indicator Group'))
    Indicator_type =models.CharField(_('Indicator Type'),choices=CATEGORIES,
        max_length=5,default=CATEGORIES[0][0])
    description = models.TextField(_('Description'),blank=True,null=True,)

    class Meta:
        managed = True
        db_table = 'stg_uhclock_indicators'
        verbose_name = _('UHC Clock Indicator')
        verbose_name_plural = _('   UHC Clock Indicators')
        ordering = ('indicator',)

    def __str__(self):
        return str(self.indicator) #display indicator name
    
    
class StgUHCIndicatorTheme(TranslatableModel):
    language = get_language_translations() # call language translation function 
    
    LEVEL = (
        (1,_('level 1')),
        (2,_('level 2')),
    )
    domain_id = models.AutoField(primary_key=True)  # Field name made lowercase.
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    translations = TranslatedFields(
        name = models.CharField(_('Theme Name'),max_length=150, blank=False,
        null=False),
        shortname = models.CharField(_('Short Name'),max_length=45,blank=False,
            null=False),
        description = models.TextField(_('Description'),blank=True,null=True,)
    )
    level =models.SmallIntegerField(_('Theme Level'),choices=LEVEL,
        default=LEVEL[0][0])
    # code = models.CharField(unique=True, max_length=45, blank=True,
    #     null=True,verbose_name = _('Code'))
    group = models.ForeignKey(StgUHClockIndicatorsGroup, models.PROTECT, blank=True, null=True,
        verbose_name = _('UHC Indicator Group')) # for chaining the indicators
      
    parent = models.ForeignKey('self', models.PROTECT, blank=True, null=True,
        verbose_name = _('Parent Theme'))  # Field name made lowercase.

    indicators = ChainedManyToManyField(
        StgUHClockIndicators,
        horizontal=True,
        blank=True,
        verbose_name = 'indicators', 
        chained_field="group",
        chained_model_field="group",
        limit_choices_to={"indicator__translations__language_code":language},
        ) # filter by language code. Discovered on 13/12/2023 after struggles 
    
    date_created = models.DateTimeField(_('Date Created'),blank=True,null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_uhclock_indicator_themes'
        verbose_name = _('UHC Theme')
        verbose_name_plural = _('  UHC Clock Themes')
        ordering = ('level',)

    def __str__(self):
        return self.name #ddisplay disagregation options

    # The filter function need to be modified to work with django parler as follows:
    def clean(self): # Don't allow end_period to be greater than the start_period.
        if StgUHCIndicatorTheme.objects.filter(
            translations__name=self.name).count() and not self.domain_id:
            raise ValidationError({'name':_('Sorry! This indicators theme exists')})

    def save(self, *args, **kwargs):
        super(StgUHCIndicatorTheme, self).save(*args, **kwargs)


class Facts_UHC_DatabaseView (models.Model):
    fact_id = models.AutoField(primary_key=True)
    indicator_id = models.PositiveIntegerField(blank=True,
        verbose_name='Indicator ID') 
    afrocode = models.CharField(_('Indicator Code'),max_length=10,
        blank=True, null=True)
    indicator = models.CharField(_('Indicator Name'),max_length=200,
        blank=True, null=True)
    location = models.CharField(max_length=500,blank=False,
        verbose_name = _('Location Name'),)
    categoryoption = models.CharField(max_length=500,blank=False,
        verbose_name =_('Disaggregation Options'))
    datasource = models.CharField(max_length=500,verbose_name = _('Data Source'))
    measure_type = models.CharField(max_length=500,blank=False,
        verbose_name =_('Measure Type'))
    value_received = DecimalField(_('Numeric Value'),max_digits=20,
        decimal_places=3,blank=True,null=True)
    start_period = models.PositiveIntegerField(
        blank=True,verbose_name='Start Year') 
    end_period = models.PositiveIntegerField(
        blank=True,verbose_name='End Year') 
    period = models.CharField(_('Period'),max_length=25,
        blank=True,null=False)
    uhclock_theme = models.CharField(_('UHC Clock Theme'),max_length=150,
        blank=True,null=False)
    comment = models.CharField(_('Status'),max_length=25,blank=True,null=False)

    class Meta:
        managed = False
        db_table = 'vw_uhc_fact_data_indicators'
        verbose_name = _('UHC Clock Fact')
        verbose_name_plural = _('   UHC Clock Facts')
        ordering = ('indicator',)

    def __str__(self):
         return str(self.indicator) 
    

class CountrySelectionUHCIndicators(models.Model):
    language = get_language_translations() # call language translation function 

    countrychoice_id = models.AutoField(primary_key=True)
    location = models.ForeignKey(StgLocation,models.PROTECT,
        verbose_name = _('Country/Location'),)
    domain = models.ManyToManyField(StgUHCIndicatorTheme,blank=False,
        verbose_name = _('UHC Clock Theme'), default = None)

    indicators = ChainedManyToManyField(
        StgUHClockIndicators,
        horizontal=True,
        blank=True,
        chained_field="domain",
        chained_model_field="group",
        limit_choices_to={"indicator__translations__language_code":language},
        ) # filter by language code. Discovered on 13/12/2023 after struggles  
        
    class Meta:
        managed = True
        db_table = 'stg_uhclock_country_indicators_selection'
        verbose_name = _('Country Selection')
        verbose_name_plural = _('UHC Clock Country Selections')
        ordering = ('location',)
    
    # import pdb; pdb.set_trace()
    def __str__(self):
        return str(self.location) 
    