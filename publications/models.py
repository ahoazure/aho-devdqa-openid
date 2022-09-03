from django.db import models
import uuid
import datetime
# from datetime import datetime #for handling year part of date filed
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _ # The _ is alias for gettext
from parler.models import TranslatableModel,TranslatedFields
from regions.models import StgLocation
from authentication.models import CustomUser
from django.core.validators import MinValueValidator, MaxValueValidator
from smart_selects.db_fields import ChainedForeignKey # supports A->-B->C lookup

def make_choices(values):
    return [(v, v) for v in values]

def current_year():
    return datetime.date.today().year

def max_value_current_year(value):
    return MaxValueValidator(current_year())(value)

# Model to take care of resource types added 11/05/2019 courtesy of Gift
class StgResourceType(TranslatableModel):
    type_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    translations = TranslatedFields(
        name = models.CharField(_('Type Name'),max_length=230, blank=False,
            null=False),  # Field name made lowercase.
        shortname = models.CharField(_('Short Name'),max_length=100, blank=True,
            null=True),
        description = models.TextField(_('Brief Description'),blank=True,
            null=True)  # Field name made lowercase.
    )
    code = models.CharField(_('Code'),unique=True, max_length=50, blank=True,
        null=True)  # Field name made lowercase.
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_resource_type'
        verbose_name = _('Resource Type')
        verbose_name_plural = _('  Resource Types')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the knowledge product category name

    def clean(self):
        if StgResourceType.objects.filter(
            translations__name=self.name).count() and not self.type_id and not \
                self.code:
            raise ValidationError({'name':_('Resource type with the same \
                name exists')})

    def save(self, *args, **kwargs):
        super(StgResourceType, self).save(*args, **kwargs)


# New model to take care of resource types added 11/05/2019 courtesy of Gift
class StgResourceCategory(TranslatableModel):
    CATEGORIES = (
        (1,'Research Products'),
        (2,'Health Workforce')
    )
    category_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(_('Code'),unique=True, max_length=50, blank=True,
        null=True)  # Field name made lowercase
    type = models.ForeignKey(StgResourceType, models.PROTECT,blank=False,
        null=False,verbose_name=_('Resource Type'),related_name='category_type')
    translations = TranslatedFields(
        name = models.CharField(_('Category Name'),max_length=230, blank=False,
            null=False),  # Field name made lowercase.
        shortname = models.CharField(_('Short Name'),max_length=100, blank=True,
            null=True),
        description = models.TextField(_('Description'),blank=True,
            null=True)  # Field name made lowercase.
    )
    category = models.SmallIntegerField(choices=CATEGORIES,
        default=CATEGORIES[0][0],verbose_name ='Classification')
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_resource_category'
        verbose_name = _('Resource Category')
        verbose_name_plural = _(' Resource Categories')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the knowledge product category name

    def clean(self):
        if StgResourceCategory.objects.filter(
            translations__name=self.name).count() and not self.category_id and not \
                self.code:
            raise ValidationError({'name':_('Resource category with the same \
                name exists')})

    def save(self, *args, **kwargs):
        super(StgResourceCategory, self).save(*args, **kwargs)


class StgKnowledgeProduct(TranslatableModel):
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    )

    product_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    user = models.ForeignKey(CustomUser, models.PROTECT,blank=True,
		verbose_name = 'User Name (Email)',) ## request helper field
    type = models.ForeignKey(StgResourceType, models.PROTECT,blank=False,
        null=False,verbose_name = _('Resource Type'))
    location = models.ForeignKey(StgLocation, models.PROTECT, blank=False,
        null=False,verbose_name = _('Resource Location'),)
    categorization = ChainedForeignKey(StgResourceCategory,
        chained_field="type",chained_model_field="type",
        show_all=False,auto_choose=True,sort=True,on_delete=models.PROTECT,
        blank=False,null=False,verbose_name=_('Resource Category'),default=1,
        related_name='category_type')
    translations = TranslatedFields(
        title = models.CharField(_('Title'),max_length=2000,blank=False,
        null=False,db_index=True),
        description = models.TextField(_('Brief Description'),blank=True, null=True),
        abstract = models.TextField(_('Abstract/Summary'),blank=True, null=True),
        author = models.CharField(_('Author/Owner'),max_length=200, blank=False,
            null=False),  # Field name made lowercase.
        year_published=models.PositiveIntegerField(_('Year Published'),
            null=False,blank=False,
            validators=[MinValueValidator(1900),max_value_current_year],
            default=current_year(),
            help_text=_("This marks year of publication")),
        internal_url = models.FileField (_('File'),upload_to='production/files/',
            blank=True,),
        external_url = models.CharField(blank=True, null=True, max_length=2083),
        cover_image = models.ImageField(_('Cover Picture'),
            upload_to='production/images/',blank=True,), # thumbnail requires pillow
        meta = {'unique_together':[('language_code','title','year_published',
            'author',)]},
    )  # End of translatable fields
    code = models.CharField(unique=True, blank=True,null=False,max_length=45)
    comment = models.CharField(_('Status'),max_length=10, choices= STATUS_CHOICES,
        default=STATUS_CHOICES[0][0])
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        permissions = (
            ("approve_stgknowledgeproduct", "Can approve Knowledge Resource"),
            ("reject_stgknowledgeproduct", "Can reject Knowledge Resource"),
            ("pend_stgknowledgeproduct", "Can pend Knowledge Resource")
        )
        managed = True
        db_table = 'stg_knowledge_product'
        verbose_name = _('Knowledge Resource')
        verbose_name_plural = _('   Knowledge Resources')
        ordering = ('translations__title',)

    def __str__(self):
        return self.title #display the data element name

    def clean(self): # Don't allow end_period to be greater than the start_period.
        import datetime
        if self.year_published <=1900 or self.year_published > datetime.date.today().year:
            raise ValidationError({'year_published':_(
                'Sorry! The publishing year cannot be lower than 1900 or \
                 greater than the current Year ')})

        if StgKnowledgeProduct.objects.filter(
            translations__title=self.title).count() and not self.product_id and not \
                self.year_published and not self.location:
            raise ValidationError({'title':_('Knowledge resource with the same \
                title already exists')})

    def save(self, *args, **kwargs):
        return super(StgKnowledgeProduct, self).save(*args, **kwargs)


class StgProductDomain(TranslatableModel):
    LEVEL = (
    (1,_('level 1')),
    (2,_('level 2')),
    (3,_('level 3')),
    (4,_('level 4')),
    (5,_('level 5')),
    (6,_('level 6')),
    )
    domain_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    translations = TranslatedFields(
        name = models.CharField(_('Resource Theme'),max_length=230, blank=False,
            null=False),
        shortname = models.CharField(_('Short Name'),max_length=45,null=True),
        description = models.TextField(_('Brief Description'),blank=True,
            null=True),
        level =models.SmallIntegerField(_('Theme Level'),choices=LEVEL,
            default=LEVEL[0][0])
        )
    code = models.CharField(_('Theme Code'),unique=True,max_length=50,
        blank=True,null=True)
    parent = models.ForeignKey('self',on_delete=models.CASCADE,
        blank=True,null=True,verbose_name = _('Parent Theme'))
    publications = models.ManyToManyField(StgKnowledgeProduct,
        db_table='stg_product_domain_members',
        blank=True,verbose_name = _('Resources'))
    date_created = models.DateTimeField(_('Date Created'),blank=True,null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True # must be true to create the model table in mysql
        db_table = 'stg_publication_domain'
        verbose_name = _('Resource Theme')
        verbose_name_plural = _('  Resource Themes')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the knowledge product category name

    def clean(self):
        if StgProductDomain.objects.filter(
            translations__name=self.name).count() and not self.domain_id and not \
                self.code:
            raise ValidationError({'name':_('Resource Theme with the same \
                name exists')})

    def save(self, *args, **kwargs):
        super(StgProductDomain, self).save(*args, **kwargs)


class StgKnowledgeResourceTagging(models.Model):
    tag_id = models.AutoField(primary_key=True)
    publications = models.ForeignKey(StgKnowledgeProduct,models.PROTECT,
                blank=False,null=False,verbose_name = _('Resource Name'))
    location = models.ForeignKey(StgLocation, models.PROTECT, blank=False,
        null=False,verbose_name = _('Tagged To:'),)

    class Meta:
        managed = True # must be true to create the model table in mysql
        db_table = 'stg_knowledge_resource_tag'
        verbose_name = _('Resource Tag')
        verbose_name_plural = _('Resource Tags')
        unique_together = ('publications','location',)
        ordering = ('location__translations__name',)

    def __str__(self):
        return str(self.publications) #display string name of knowledge product

    def save(self, *args, **kwargs):
        super(StgKnowledgeResourceTagging,self).save(*args, **kwargs)
