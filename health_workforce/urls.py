from rest_framework.routers import SimpleRouter
from health_workforce import views # import the views for routing on the api endpoints

router = SimpleRouter()
router.register(
    r'courses', views.StgInstitutionProgrammesViewSet,'course')
router.register(
    r'training_types',views.StgInstitutionTypeViewSet,'training_type')
router.register(
    r'institutions', views.StgTrainingInstitutionViewSet,'institution')
router.register(r'cadres', views.StgHealthCadreViewSet,'carde')
router.register(
    r'workforce',views.StgHealthWorkforceFactsViewSet,'workforce')
urlpatterns = router.urls
