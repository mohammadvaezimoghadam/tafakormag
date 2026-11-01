from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PostViewSet, TopicViewSet, ImportTaskViewSet, TopicFAQViewSet,
    PostEditProposalViewSet, PostEditHistoryViewSet
)

router = DefaultRouter()
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'import-tasks', ImportTaskViewSet, basename='import-task')
router.register(r'faqs', TopicFAQViewSet, basename='faq')
router.register(r'editorial/proposals', PostEditProposalViewSet, basename='editorial-proposal')
router.register(r'editorial/history', PostEditHistoryViewSet, basename='editorial-history')
router.register(r'', PostViewSet, basename='post')

urlpatterns = [
    path('', include(router.urls)),
]