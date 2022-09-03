from tabnanny import check
from django.db import models

from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.fields import DecimalField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_pandas.managers import DataFrameManager

from parler.models import TranslatableModel, TranslatedFields
from home.models import (
    StgDatasource,StgCategoryoption,StgMeasuremethod,
    StgValueDatatype)
from regions.models import StgLocation
from authentication.models import CustomUser

from indicators.models import StgIndicator

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


class Facts_DataFrame (models.Model):
    fact_id = models.AutoField(primary_key=True)
    user = models.PositiveIntegerField(blank=True,verbose_name='UserID') # request helper field
    afrocode = models.CharField(_('Indicator ID'),max_length=1500,
        blank=True, null=True)
    indicator_name = models.CharField(_('Indicator Name'),max_length=1500,
        blank=True, null=True)
    location = models.CharField(max_length=1500,blank=False,
        verbose_name = _('Location Name'),)
    categoryoption = models.CharField(max_length=1500,blank=False,
        verbose_name =_('Disaggregation Options'))
    datasource = models.CharField(max_length=1500,verbose_name = _('Data Source'))
    measure_type = models.CharField(max_length=1500,blank=False,
        verbose_name =_('Measure Type'))
    value = DecimalField(_('Numeric Value'),max_digits=20,
        decimal_places=3,blank=True,null=True)
    period = models.CharField(_('Period'),max_length=25,blank=True,null=False)
    objects = DataFrameManager() #connect the model to the dataframe manager

    class Meta:
        managed = False
        db_table = 'dqa_vw_facts_dataframe'
        verbose_name = _('Facts')
        verbose_name_plural = _('   Facts')
        ordering = ('indicator_name',)

    def __str__(self):
         return str(self.indicator_name)    


# The following model is used to validate measure types in the fact table
class MeasureTypes_Validator(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    afrocode = models.CharField(_('Indicator ID'),max_length=50,
        blank=True, null=True)
    indicator_name = models.CharField(_('Indicator Name'),max_length=1500,
        blank=True, null=True)
    measure_type = models.CharField(_('Measure Type'),max_length=500,
        blank=True, null=True)
    measuremethod_id = models.PositiveIntegerField(_('Measure Type ID'),
        blank=True,null=True)
    objects = DataFrameManager() #connect the model to the dataframe manager

    class Meta:
        managed = True
        db_table = 'dqa_valid_measure_type'
        verbose_name = _('Valid Measure Type')
        verbose_name_plural = _('  Measuretypes')
        ordering = ('indicator_name',)

    def __str__(self):
         return self.indicator_name
    

# The following model is used to validate data sources in the fact table
class DataSource_Validator(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    afrocode = models.CharField(_('Indicator ID'),max_length=50,
        blank=True, null=True)
    indicator_name = models.CharField(_('Indicator Name'),max_length=1500,
        blank=True, null=True)
    datasource = models.CharField(_('Data Source'),max_length=500,
        blank=True, null=True)
    datasource_id = models.PositiveIntegerField(_('Data SourceID'),
        blank=True,null=True)
    objects = DataFrameManager() #connect the model to the dataframe manager


    class Meta:
        managed = True
        db_table = 'dqa_valid_datasources'
        verbose_name = _('Valid Source')
        verbose_name_plural = _('  Datasources')
        ordering = ('indicator_name',)

    def __str__(self):
         return self.indicator_name
    

# The following model is used to validate categoryoptions in the fact table
class CategoryOptions_Validator(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field  
    afrocode = models.CharField(_('Indicator ID'),max_length=50,
        blank=True, null=True)
    indicator_name = models.CharField(_('Indicator Name'),max_length=1500,
        blank=True, null=True)
    categoryoption = models.CharField(_('Disaggregation Name'),max_length=500,
        blank=True, null=True)
    categoryoption_id = models.PositiveIntegerField(_('Disaggregation ID'),
        blank=True,null=True)
    objects = DataFrameManager() #connect the model to the dataframe manager
 

    class Meta:
        managed = True
        db_table = 'dqa_valid_categoryoptions'
        verbose_name = _('Valid Category Option')
        verbose_name_plural = _('  Categoryoptions')
        ordering = ('indicator_name',)

    def __str__(self):
         return self.indicator_name
    

class Similarity_Index(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    source_indicator = models.CharField(_('Data Indicator'),max_length=2000,
        blank=True, null=True)
    similar_indicator = models.CharField(_('Similar Indicator'),max_length=2000,
        blank=True, null=True)
    score = models.PositiveIntegerField(_('Similarity Score %'),
        blank=False,null=False)
    objects = DataFrameManager() #connect the model to the dataframe manager


    class Meta:
        managed = True
        db_table = 'dqa_similar_indicators_score'
        verbose_name = _('Similarity Score')
        verbose_name_plural = _('Similarity Scores')
        ordering = ('-score',)

    def __str__(self):
         return self.source_indicator


class MeasureType_Statistics(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    location = models.CharField(_('Country'),max_length=2000,
        blank=True, null=True)
    indicator_name = models.CharField(_('Indicator Name'),max_length=2000,
        blank=True, null=True)
    count = models.PositiveIntegerField(_('Number of Measure Types'),
        blank=False,null=False)
    objects = DataFrameManager() #connect the model to the dataframe manager


    class Meta:
        managed = True
        db_table = 'dqa_multiple_indicators_statistics'
        verbose_name = _('Measure Types Summary')
        verbose_name_plural = _('Measure Summaries')
        ordering = ('-count',)

    def __str__(self):
         return self.location
   


class Mutiple_MeasureTypes(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    indicator_name = models.CharField(_('Indicator Name'),max_length=2000,
        blank=True, null=True,editable=False)
    location = models.CharField(_('Country'),max_length=2000,
        blank=True, null=True,editable=False)
    categoryoption = models.CharField(_('category Option'),max_length=2000,
        blank=True, null=True,editable=False)
    datasource = models.CharField(_('Data Source'),max_length=2000,
        blank=True, null=True,editable=False)
    measure_type = models.CharField(_('Measure Type'),max_length=2000,
        blank=True, null=True,editable=False)
    value = DecimalField(_('Value Received'),max_digits=20,decimal_places=3,
        blank=True,null=True,editable=False)
    period = models.CharField(_('Period'),max_length=2000,
        blank=True, null=True,editable=False)
    counts = models.PositiveIntegerField(_('Number of Measure Types'),
        blank=True,null=True,editable=False) 
    remarks = models.CharField(_('Remarks'),max_length=2000,
        blank=True, null=True)  
    objects = DataFrameManager() #connect the model to the dataframe manager
   
    class Meta:
        managed = True
        db_table = 'dqa_multiple_indicators_checker'
        verbose_name = _('Multiple Multiple Type')
        verbose_name_plural = _('Multiple Measures')
        ordering = ('indicator_name',)

    def __str__(self):
         return self.indicator_name


# ---------------------------data validation models from algorithms 1-4-------------------------------------------------

class DqaInvalidCategoryoptionRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    indicator_name = models.CharField(blank=True, null=True,max_length=2000,)
    location = models.CharField(blank=True, null=True,max_length=2000,)
    categoryoption = models.CharField(blank=True, null=True,max_length=2000,)
    datasource = models.CharField(blank=True, null=True,max_length=2000,)
    measure_type = models.CharField(blank=True, null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(blank=True, null=True,max_length=2000,)
    check_category_option = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'dqa_invalid_categoryoption_remarks'
        verbose_name = _('Check Categoryoption')
        verbose_name_plural = _(' Check Categories')
        ordering = ('indicator_name',)

    def __str__(self):
        return self.indicator_name


class DqaInvalidDatasourceRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    indicator_name = models.CharField(blank=True, null=True,max_length=2000,)
    location = models.CharField(blank=True, null=True,max_length=2000,)
    categoryoption = models.CharField(blank=True, null=True,max_length=2000,)
    datasource = models.CharField(blank=True, null=True,max_length=2000,)
    measure_type = models.CharField(db_column='measure type', 
        blank=True, null=True,max_length=2000,) 
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(blank=True,null=True,max_length=2000,)
    check_data_source = models.TextField(blank=True, null=True) 

    class Meta:
        managed = True
        db_table = 'dqa_invalid_datasource_remarks'
        verbose_name = _('Invalid Source')
        verbose_name_plural = _(' Check Sources')
        ordering = ('indicator_name',)

    def __str__(self):
        return self.indicator_name
        

class DqaInvalidMeasuretypeRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    indicator_name = models.CharField(blank=True,null=True,max_length=2000,)
    location = models.CharField(blank=True, null=True,max_length=2000,)
    categoryoption = models.CharField(blank=True, null=True,max_length=2000,)
    datasource = models.CharField(blank=True, null=True,max_length=2000,)
    measure_type = models.CharField(blank=True, null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(blank=True, null=True,max_length=2000,)
    check_mesure_type = models.TextField(blank=True, null=True) 

    class Meta:
        managed = True
        db_table = 'dqa_invalid_measuretype_remarks'
        verbose_name = _('Check Measutype')
        verbose_name_plural = _(' Check Measures')
        ordering = ('indicator_name',)

    def __str__(self):
        return self.indicator_name


class DqaInvalidPeriodRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    indicator_name = models.CharField(blank=True, null=True,max_length=2000,)
    location = models.CharField(blank=True, null=True,max_length=2000,)
    categoryoption = models.CharField(blank=True, null=True,max_length=2000,)
    datasource = models.CharField(blank=True, null=True,max_length=2000,)
    measure_type = models.CharField(blank=True, null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(blank=True, null=True,max_length=2000,)
    check_year = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'dqa_invalid_period_remarks'
        verbose_name = _('Check Period')
        verbose_name_plural = _(' Check Periods')
        ordering = ('indicator_name',)
    

    def __str__(self):
        return self.indicator_name


class DqaExternalConsistencyOutliersRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    indicator_name = models.CharField(blank=True, null=True,max_length=2000,)
    location = models.CharField(blank=True, null=True,max_length=2000,)
    categoryoption = models.CharField(blank=True, null=True,max_length=2000,)
    datasource = models.CharField(blank=True, null=True,max_length=2000,)
    measure_type = models.CharField(blank=True, null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(blank=True, null=True,max_length=2000,)
    external_consistency = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'dqa_external_inconsistencies_remarks'
        verbose_name = _('External Consistency')
        verbose_name_plural = _('External Consistencies')
        ordering = ('indicator_name',)
    
    def __str__(self):
        return self.indicator_name


class DqaInternalConsistencyOutliersRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    indicator_name = models.CharField(blank=True, null=True,max_length=2000,)
    location = models.CharField(blank=True, null=True,max_length=2000,)
    categoryoption = models.CharField(blank=True, null=True,max_length=2000,)
    datasource = models.CharField(blank=True, null=True,max_length=2000,)
    measure_type = models.CharField(blank=True, null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(blank=True, null=True,max_length=2000,)
    internal_consistency = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'dqa_internal_consistencies_remarks'
        verbose_name = _('Internal Consistency')
        verbose_name_plural = _('Internal Consistencies')
        ordering = ('indicator_name',)
    
    def __str__(self):
        return self.indicator_name

class DqaValueTypesConsistencyRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)',default=14) # request helper field
    indicator_name = models.CharField(blank=True, null=True,max_length=2000,)
    location = models.CharField(blank=True, null=True,max_length=2000,)
    categoryoption = models.CharField(blank=True, null=True,max_length=2000,)
    datasource = models.CharField(blank=True, null=True,max_length=2000,)
    measure_type = models.CharField(blank=True, null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(blank=True, null=True,max_length=2000,)
    check_value = models.TextField(blank=True, null=True,max_length=2000,)

    class Meta:
        managed = True
        db_table = 'dqa_valuetype_consistencies_remarks'
        verbose_name = _('Value Consistency')
        verbose_name_plural = _('Value Consistencies')
        ordering = ('indicator_name',)
    
    def __str__(self):
        return self.indicator_name