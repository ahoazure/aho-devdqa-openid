from rest_framework.serializers import ModelSerializer
from parler_rest.serializers import TranslatableModelSerializer
from .models import (StgDatasource, StgCategoryParent,
    StgCategoryoption,StgValueDatatype,StgMeasuremethod,)


class StgDisagregationCategorySerializer(TranslatableModelSerializer):
    class Meta:
        model = StgCategoryParent
        fields = ['uuid', 'name', 'shortname', 'code', 'description',]


class StgDisagregationOptionsSerializer(TranslatableModelSerializer):
    class Meta:
        model = StgCategoryoption
        fields = ['uuid', 'category','name', 'shortname', 'code',
                'description']

class StgDatasourceSerializer(TranslatableModelSerializer):
    class Meta:
        model = StgDatasource
        fields = ['uuid', 'name', 'shortname', 'code','description']


class StgValueDatatypeSerializer(TranslatableModelSerializer):
    class Meta:
        model = StgValueDatatype
        fields = ['uuid', 'name', 'shortname', 'code','description']


class StgMeasuremethodSerializer(TranslatableModelSerializer):
    class Meta:
        model = StgMeasuremethod
        fields = ['uuid', 'name', 'code','description']
