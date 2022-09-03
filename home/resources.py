import random
from import_export import resources
from .models import (StgCategoryParent,StgDatasource,
    StgCategoryoption, StgValueDatatype)
from import_export.fields import Field

class AuthRouter(object):
    """
    A router to control all database operations on models in the
    auth application.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read auth models go to default.
        """
        if model._meta.app_label == 'auth':
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth models go to default.
        """
        if model._meta.app_label == 'auth':
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the auth app is involved.
        """
        if obj1._meta.app_label == 'auth' or \
           obj2._meta.app_label == 'auth':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth app only appears in the 'default'
        database.
        """
        if app_label == 'auth':
            return db == 'default'
        return None


class PrimaryReplicaRouter(object):
    def db_for_read(self, model, **hints):
        """
        Reads go to a randomly-chosen replica.
        """
        return random.choice(['replica1', 'replica2'])

    def db_for_write(self, model, **hints):
        """
        Writes always go to aho_data.
        """
        return 'aho_data'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the aho_data/replica pool.
        """
        db_list = ('aho_data', 'replica1', 'replica2')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        All non-auth models end up in this pool.
        """
        return True


class DisaggregateCategoryExport(resources.ModelResource):
    category_name = Field(
        attribute='name', column_name='Category Name')
    category_code= Field(
        attribute='code', column_name='Category Code')
    shortname = Field(
        attribute='shortname', column_name='Short Name')
    description = Field(
        attribute='description', column_name='Description')

    class Meta:
        model = StgCategoryParent
        skip_unchanged = False
        report_skipped = False
        fields = ('category_name','category_code','shortname', 'description',)


class DisaggregateOptionExport(resources.ModelResource):
    disaggregation_name = Field(
        attribute='name', column_name='Disaggregation Name')
    disaggregation_code= Field(
        attribute='code', column_name='Disaggregation Code')
    category = Field(
        attribute='category__name', column_name='Disaggregation Category')
    shortname = Field(
        attribute='shortname', column_name='Short Name')
    description = Field(
        attribute='description', column_name='Description')

    class Meta:
        model = StgCategoryoption
        skip_unchanged = False
        report_skipped = False
        fields = ('disaggregation_name','disaggregation_code','category',
            'shortname', 'description',)


class MeasureTypeExport(resources.ModelResource):
    measure_name = Field(
        attribute='name', column_name='Measure Name')
    measure_code= Field(
        attribute='code', column_name='Measure Code')
    shortname = Field(
        attribute='shortname', column_name='Short Name')
    description = Field(
        attribute='description', column_name='Description')

    class Meta:
        model = StgCategoryoption
        skip_unchanged = False
        report_skipped = False
        fields = ('measure_name','measure_code','shortname', 'description',)


class DataTypeExport(resources.ModelResource):
    name = Field(
        attribute='name', column_name='Measure Name')
    datatype_code= Field(
        attribute='code', column_name='Measure Code')
    shortname = Field(
        attribute='shortname', column_name='Short Name')
    description = Field(
        attribute='description', column_name='Description')

    class Meta:
        model = StgValueDatatype
        skip_unchanged = False
        report_skipped = False
        fields = ('name','datatype_code','shortname', 'description',)

class DataSourceExport(resources.ModelResource):
    name = Field(
        attribute='name', column_name='Data Source Name')
    datasource_code= Field(
        attribute='code', column_name='Data Source Code')
    shortname = Field(
        attribute='shortname', column_name='Short Name')
    description = Field(
        attribute='description', column_name='Description')

    class Meta:
        model = StgDatasource
        skip_unchanged = False
        report_skipped = False
        fields = ('name','datasource_code','shortname','description',)
