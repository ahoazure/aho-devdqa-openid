from rest_framework.routers import SimpleRouter
from regions import views

router = SimpleRouter()
router.register(
    r'location_level', views.StgLocationLevelViewSet, "location_level")
router.register(
    r'economic_zones', views.StgEconomicZonesViewSet, "economic_zone"),
router.register(
    r'income_levels', views.StgWorldbankIncomegroupsViewSet, "income_level"),
router.register(
    r'locations', views.StgLocationViewSet, "location")
urlpatterns = router.urls
