from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import pre_save,post_save
import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.fields import DecimalField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields
from home.models import (StgDatasource,StgCategoryoption,StgMeasuremethod,
    StgValueDatatype)
from indicators.models import StgIndicator
from authentication.models import CustomUser


class StgUHCIndicatorGroup(TranslatableModel):
    domain_id = models.AutoField(primary_key=True)  # Field name made lowercase.
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    translations = TranslatedFields(
        name = models.CharField(_('UHC Clock Theme'),max_length=150, blank=False,
        null=False),
        shortname = models.CharField(_('Short Name'),max_length=45,blank=False,
            null=False),
        description = models.TextField(_('Brief Description'),blank=True,null=True,)
    )
    code = models.CharField(unique=True, max_length=45, blank=True,
        null=True,verbose_name = _('Code'))
    # this field establishes a many-to-many relationship with the domain table
    indicators = models.ManyToManyField(StgIndicator,
        db_table='stg_uhc_clock_domain_members',blank=True,
        verbose_name = _('Indicators'))  # Field name made lowercase.
    date_created = models.DateTimeField(_('Date Created'),blank=True,null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_uhc_indicator_themes'
        verbose_name = _('UHC Theme')
        verbose_name_plural = _(' UHC Themes')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #ddisplay disagregation options

    # The filter function need to be modified to work with django parler as follows:
    def clean(self): # Don't allow end_period to be greater than the start_period.
        if StgUHCIndicatorGroup.objects.filter(
            translations__name=self.name).count() and not self.domain_id:
            raise ValidationError({'name':_('Sorry! This indicators theme exists')})

    def save(self, *args, **kwargs):
        super(StgUHCIndicatorGroup, self).save(*args, **kwargs)



class Facts_UHC_DatabaseView (models.Model):
    fact_id = models.AutoField(primary_key=True)
    uhc_theme = models.CharField(_('UHC Theme'),max_length=500,
        blank=True, null=True)
    indicator_code = models.CharField(_('Indicator Code'),max_length=10,
        blank=True, null=True)
    indicator_name = models.CharField(_('Indicator Name'),max_length=200,
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
    period = models.CharField(_('Period'),max_length=25,blank=True,null=False)
    comment = models.CharField(_('Status'),max_length=25,blank=True,null=False)

    class Meta:
        managed = False
        db_table = 'vw_uhc_clock_fact_indicators'
        verbose_name = _('UHC Fact')
        verbose_name_plural = _(' UHC Facts')
        ordering = ('indicator_name',)

    def __str__(self):
         return str(self.indicator_name) 