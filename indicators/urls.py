from rest_framework.routers import SimpleRouter
from indicators import views

router = SimpleRouter()
router.register(
    r'indicator_references', views.StgIndicatorReferenceViewSet, "indicator_reference")
router.register(
    r'indicators', views.StgIndicatorViewSet, "indicator")
router.register(
    r'indicator_domains', views.StgIndicatorDomainViewSet, "indicator_domain")
router.register(
    r'indicator_data', views.FactDataIndicatorViewSet, "indicator_data")
router.register(
    r'indicators_archive', views.FactIndicatorArchiveViewSet, "indicators_archive")
urlpatterns = router.urls
