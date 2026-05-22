from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NoteViewSet, ChannelViewSet

router = DefaultRouter()
router.register(r'', NoteViewSet, basename='note')
router.register(r'channel', ChannelViewSet, basename='channel')

urlpatterns = [
    path('', include(router.urls)),
]