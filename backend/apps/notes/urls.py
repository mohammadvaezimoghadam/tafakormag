from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, TopicViewSet, ImportTaskViewSet

router = DefaultRouter()
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'import-tasks', ImportTaskViewSet, basename='import-task')
router.register(r'', PostViewSet, basename='post')

urlpatterns = [
    path('', include(router.urls)),
]