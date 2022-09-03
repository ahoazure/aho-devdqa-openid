from rest_framework.routers import SimpleRouter
from facilities import views # import the views for routing on the api endpoints

router = SimpleRouter()
router.register(
    r'facility_types', views.StgFacilityTypeViewSet,'facility_type')
router.register(
    r'facility_owners',views.StgFacilityOwnershipViewSet,'facility_owner')
router.register(
    r'service_domains', views.StgServiceDomainViewSet,'service_domain')
router.register(
    r'facilities', views.StgHealthFacilityViewSet,'facility')
router.register(
    r'service_availability',views.FacilityServiceAvailabilityViewSet,
    'service_availability')
router.register(
    r'service_capacity',views.FacilityServiceAvailabilityViewSet,
    'service_capacity')
router.register(
    r'service_readiness',views.FacilityServiceAvailabilityViewSet,
    'service_readiness')
urlpatterns = router.urls
