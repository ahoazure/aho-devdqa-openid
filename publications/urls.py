from rest_framework.routers import SimpleRouter
from publications import views

router = SimpleRouter()
router.register(
    r'resource_types', views.StgResourceTypeViewSet, 'resource_type')
router.register(
    r'product_domains', views.StgKnowledgeDomainViewSet,'product_domain')
router.register(
    r'knowledge_products',views.StgKnowledgeProductViewSet,'knowledge_product')
urlpatterns = router.urls
