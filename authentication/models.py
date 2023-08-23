"""
The classes in this module overrides native  User,Group and ObectManager.
"""
from email.policy import default
from django.db import models
from django.contrib.auth.models import Group,AbstractUser,BaseUserManager
from django.utils.translation import gettext_lazy as _ # The _ is alias for gettext
from regions.models import StgLocation

def make_choices(values):
    return [(v, v) for v in values]

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('New user must be DCT admin staff.'))
        if extra_fields.get('is_active') is not True:
            raise ValueError(_('New user account must be actived.'))

        if not email:
            raise ValueError(_('Valid Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)



"""
This model class overrides the original Django user model.
"""
class CustomUser(AbstractUser):
    GENDER = ( 'Male','Female', 'Other')
    TITLE = ( 'Mr.','Ms.', 'Mrs.','Dr.', 'Prof.', 'Other')
    title = models.CharField(_('title'),choices=make_choices(TITLE),
        max_length=45,default=GENDER[0])  # Field name made lowercase.
    gender = models.CharField(_('gender'),choices=make_choices(GENDER),
        max_length=45,default=GENDER[0])  # Field name made lowercase.
    email = models.EmailField(_('e-mail'),unique=True,blank=False,null=False)
    postcode = models.CharField(_('postal code'),blank=True, null=True,
        max_length=6)
    username = models.CharField(_('user name'),blank=False, null=False,
        max_length=150)
    location = models.ForeignKey(StgLocation, models.PROTECT,default=None,
        verbose_name = _('Location Name'))  # Field name made lowercase.
    date_created = models.DateTimeField(blank=True, null=True, auto_now_add=True,
        verbose_name = _('Date Created'))
    date_lastupdated = models.DateTimeField(blank=True, null=True, auto_now=True,
        verbose_name = _('Date Modified'))

    USERNAME_FIELD = 'email' # Replaced using username as unique identifier
    REQUIRED_FIELDS = ['username','location',]

    objects = CustomUserManager()

    class Meta:
        managed = True
        verbose_name = _('User')
        verbose_name_plural = _('  User Accounts')
        ordering = ('username', )

    def __str__(self):
        return self.email


"""
This model class overrides the original Django Users Group auth model.
"""
class CustomGroup(Group):
    role = models.OneToOneField('auth.Group', parent_link=True,unique=True,
        on_delete=models.CASCADE,verbose_name=_('System Role'))
    roles_manager = models.ForeignKey(CustomUser, models.PROTECT,
        verbose_name='Logged Admin',related_name='roles_admin') # request helper field
    location = models.ForeignKey(StgLocation, models.PROTECT,
        verbose_name = _('Location Name'))  # Field name made lowercase.
    date_created = models.DateTimeField(blank=True, null=True,auto_now_add=True,
        verbose_name = _('Date Created'))
    date_lastupdated = models.DateTimeField(blank=True, null=True,auto_now=True,
        verbose_name = _('Date Modified'))

    class Meta:
        managed = True
        verbose_name = _('System Role')
        verbose_name_plural = _(' System Roles')


# This model class maps to a database View that looks up the django_admin logs,
# location, customuser and group hence reason its managed meta is False
class AhodctUserLogs(models.Model):
    username = models.CharField(_('Username'),blank=False, null=False,
        max_length=150)
    email = models.EmailField(unique=True,blank=False, null=False)
    first_name = models.CharField(max_length=30, blank=True,
        verbose_name=_("First Name"))
    last_name= models.CharField(max_length=150, blank=True,
        verbose_name=_("Last Name"))
    location_translation = models.CharField(max_length=230, blank=True,
        verbose_name=_("Location "))
    app_label = models.CharField(max_length=150, blank=True,
        verbose_name=_("Menu Executed"))
    record_name= models.CharField(max_length=200, blank=True,
        default=_("Affected Record"))
    action= models.CharField(max_length=9, blank=True,
        default=_("Action Taken"))
    action_time=models.DateTimeField(blank=True,
        verbose_name = _('Action Timestamp'))
    last_login = models.DateTimeField(blank=True,
        verbose_name = _('Last Login Timestamp'))

    class Meta:
        managed = False
        db_table = 'dct_users_log'
        verbose_name = _('View Users Log')
        verbose_name_plural = _(' View User Logs')
        ordering = ('username', )

    def __str__(self):
        return self.first_name
