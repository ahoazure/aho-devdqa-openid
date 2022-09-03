from rest_framework.routers import SimpleRouter
from health_services import views

router = SimpleRouter()
router.register(
    r'health_services_continuity', views.HealthServicesFactViewSet, "health_services")
urlpatterns = router.urls
