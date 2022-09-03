from django.urls import path
from .views import check_data_quality

app_name = 'data_quality'

urlpatterns = [
    path('', check_data_quality, name='check')
]