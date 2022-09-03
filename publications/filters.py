from django.db.models.fields import Field
from django.utils.translation import gettext_lazy as _
from django_admin_listfilter_dropdown.filters import (
    RelatedOnlyDropdownFilter)

class TranslatedFieldFilter(RelatedOnlyDropdownFilter):
    def choices(self, changelist):
        yield {
            'selected': self.lookup_val is None and not self.lookup_val_isnull,
            'query_string': changelist.get_query_string(
                remove=[self.lookup_kwarg, self.lookup_kwarg_isnull]),
            'display': _('All'),
        }
        for pk_val, val in  list(set(self.lookup_choices)):
            yield {
                'selected': self.lookup_val == str(pk_val),
                'query_string': changelist.get_query_string(
                {self.lookup_kwarg: pk_val}, [self.lookup_kwarg_isnull]),
                'display': val,
            }
        if self.include_empty_choice:
            yield {
                'selected': bool(self.lookup_val_isnull),
                'query_string': changelist.get_query_string(
                {self.lookup_kwarg_isnull: 'True'}, [self.lookup_kwarg]),
                'display': self.empty_value_display,
            }
