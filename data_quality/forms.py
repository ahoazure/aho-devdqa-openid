# import form class from django
from django import forms
# import GeeksModel from models.py
from .models import Facts_DataFilter
from regions.models import StgLocation,StgLocationLevel
from indicators.models import StgIndicator
from home.models import StgCategoryoption,StgDatasource
from aho_datacapturetool import settings

# create a ModelForm
class FilterForm(forms.ModelForm):
	class Meta:
		model = Facts_DataFilter
		fields = "__all__"
            