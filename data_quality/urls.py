from django.urls import path
from .views import check_data_quality,load_data_validators

app_name = 'data_quality'

urlpatterns = [
    path('check-quality/', check_data_quality, name='quality_validation'),
    path('load-validators/', load_data_validators, name='load_validators')
]