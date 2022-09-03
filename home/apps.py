from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _ # The _ is alias for gettext

class HomeConfig(AppConfig):
    name = 'home'
    verbose_name = _('home')
