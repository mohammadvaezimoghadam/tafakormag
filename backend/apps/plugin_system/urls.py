"""
URL Routing for Tafakor Plugin System (`/api/plugins/`).
"""
from django.urls import path
from .views import (
    PluginMarketplaceListView,
    PluginDetailView,
    PluginUserInstallView,
    PluginUserUninstallView,
    PluginUserToggleView,
    TopicPluginListView,
    TopicPluginInstallView,
    TopicPluginToggleView,
    TopicPluginUninstallView,
    PostPluginReferenceListCreateView,
)

urlpatterns = [
    # Topic Plugin Management (Must precede <str:identifier> to prevent routing collisions)
    path('topics/<int:topic_id>/', TopicPluginListView.as_view(), name='topic-plugin-list'),
    path('topics/<int:topic_id>/install/', TopicPluginInstallView.as_view(), name='topic-plugin-install'),
    path('topics/<int:topic_id>/toggle/', TopicPluginToggleView.as_view(), name='topic-plugin-toggle'),
    path('topics/<int:topic_id>/uninstall/', TopicPluginUninstallView.as_view(), name='topic-plugin-uninstall'),

    # Post References
    path('posts/<int:post_id>/references/', PostPluginReferenceListCreateView.as_view(), name='post-plugin-reference-list-create'),

    # Marketplace & User Plugin Lifecycle
    path('', PluginMarketplaceListView.as_view(), name='plugin-marketplace-list'),
    path('<str:identifier>/', PluginDetailView.as_view(), name='plugin-detail'),
    path('<str:identifier>/install/', PluginUserInstallView.as_view(), name='plugin-user-install'),
    path('<str:identifier>/uninstall/', PluginUserUninstallView.as_view(), name='plugin-user-uninstall'),
    path('<str:identifier>/toggle/', PluginUserToggleView.as_view(), name='plugin-user-toggle'),
]
