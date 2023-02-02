from admin_auto_filters.filters import AutocompleteFilter
from django.shortcuts import reverse

class LocationFilter(AutocompleteFilter):
    title = 'Country or Region Name' # display title eg By Country or Region Name
    field_name = 'location' # name of the foreign key field from child model

    def get_autocomplete_url(self, request, model_admin):
        return reverse('admin:custom_search')


class IndicatorsFilter(AutocompleteFilter):
    title = 'Indicator Name' # display title eg By Country or Region Name
    field_name = 'indicator' # name of the foreign key field from child model


class DatasourceFilter(AutocompleteFilter):
    title = 'Data Source Name' # display title eg By Country or Region Name
    field_name = 'datasource' # name of the foreign key field from child model


class CategoryOptionFilter(AutocompleteFilter):
    title = 'Disaggregation Option' # display title eg By Country or Region Name
    field_name = 'categoryoption' # name of the foreign key field from child model


class ApprovalFilter(AutocompleteFilter):
    title = 'Approval Status' # display title eg By Country or Region Name
    field_name = 'comment' # name of the foreign key field from child model