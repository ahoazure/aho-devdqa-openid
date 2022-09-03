from rest_framework.routers import SimpleRouter
from elements import views

router = SimpleRouter()
router.register(
    r'data_elements', views.StgDataElementViewSet, "data_element")
router.register(
    r'raw_data', views.FactDataElementViewSet, "raw_data")
urlpatterns = router.urls
