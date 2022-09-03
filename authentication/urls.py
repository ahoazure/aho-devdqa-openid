from django.urls import re_path, path
from authentication.views import (microsoft_login,microsoft_logout,callback,)

app_name = 'microsoft_authentication'#renamed authntication app to match callbacks

urlpatterns = [
    path('login', microsoft_login, name="microsoft_authentication_login"),
    path('logout', microsoft_logout, name="microsoft_authentication_logout"),
    path('callback', callback, name="microsoft_authentication_callback"),
]
