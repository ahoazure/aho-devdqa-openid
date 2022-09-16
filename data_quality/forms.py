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
	# language_code = settings.LANGUAGE_CODE
	class Meta:
		model = Facts_DataFilter
		fields = "__all__"

	def __init__ (self, *args, **kwargs):
		super(FilterForm, self).__init__(*args, **kwargs)
		# self.fields["locations"].widget = forms.widgets.CheckboxSelectMultiple()
		self.fields["locations"].queryset = StgLocation.objects.filter(
            locationlevel__locationlevel_id__gte=1,
            locationlevel__locationlevel_id__lte=2).filter(
                translations__language_code='en')
		self.fields["indicators"].queryset = StgIndicator.objects.filter(
            translations__language_code='en')
		self.fields["categoryoptions"].queryset = StgCategoryoption.objects.filter(
            translations__language_code='en')
		self.fields["datasource"].queryset = StgDatasource.objects.filter(
            translations__language_code='en')
            