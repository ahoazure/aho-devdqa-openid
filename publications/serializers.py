from rest_framework.serializers import (
    ModelSerializer, ReadOnlyField)
from parler_rest.serializers import TranslatableModelSerializer
from parler_rest.fields import TranslatedFieldsField
from django.utils.translation import get_language_from_request

from aho_datacapturetool import settings
from publications.models import (StgResourceType,StgKnowledgeProduct,
    StgProductDomain)

"""
Mixin class for selecting only requested translation with django-parler-rest
"""
class TranslatedSerializerMixin(object):

    def to_representation(self, instance): # override to_representation method
        inst_rep = super().to_representation(instance)
        request = self.context.get('request')
        lang_code = get_language_from_request(request)
        result = {} # initialize a blank dictionary
        for field_name, field in self.get_fields().items():
            # add normal field to resulting representation
            if field_name is not 'translations':
                field_value = inst_rep.pop(field_name)
                result.update({field_name: field_value})
            if field_name is 'translations':
                translations = inst_rep.pop(field_name)
                if lang_code not in translations:
                    # use fallback setting in PARLER_LANGUAGES
                    parler_default_settings = settings.PARLER_LANGUAGES['default']
                    if 'fallback' in parler_default_settings:
                        lang_code = parler_default_settings.get('fallback')

                    if 'fallbacks' in parler_default_settings:
                        lang_code = parler_default_settings.get('fallbacks')[0]
                for lang, translation_fields in translations.items():
                    if lang == lang_code:
                        trans_rep = translation_fields.copy()  # make copy to use pop() from
                        for trans_field_name, trans_field in translation_fields.items():
                            field_value = trans_rep.pop(trans_field_name)
                            result.update({trans_field_name: field_value})
        return result # return data based on the request object's language code


class StgResourceTypeSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=StgResourceType)

    class Meta:
        model = StgResourceType
        fields = ['uuid','code','translations']


class StgKnowledgeDomainSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=StgProductDomain)

    class Meta:
        model = StgProductDomain
        fields = ['uuid', 'code','parent','translations']


class StgKnowledgeProductSerializer(TranslatedSerializerMixin,TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=StgKnowledgeProduct)
    location_name = ReadOnlyField(source='location.name')
    class Meta:
        model = StgKnowledgeProduct
        fields = ['uuid','title','code','type','categorization','location',
                    'location_name','translations',]
