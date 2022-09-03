from rest_framework.routers import SimpleRouter
from home import views

router = SimpleRouter()

router.register(
    r'disagregation_categories',views.StgDisagregationCategoryViewSet,
    "disagregation_category",)
router.register(
    r'disagregation_options',views.StgDisagregationOptionsViewSet,
    "disagregation_option")
router.register(
    r'data_sources', views.StgDatasourceViewSet, "data_source")
router.register(
    r'value_types', views.StgValueDatatypeViewSet, "value_type")
router.register(
    r'measure_types', views.StgMeasuremethodViewSet, "measure_type")
urlpatterns = router.urls
