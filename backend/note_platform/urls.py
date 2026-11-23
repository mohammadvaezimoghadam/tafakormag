"""
URL configuration for note_platform project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.http import JsonResponse
from plugins.quran.khatm_views import KhatmWebPreviewView



def assetlinks_view(request):
    """Serves Android Digital Asset Links for app deep linking verification."""
    return JsonResponse([
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "com.example.tafakor_shop",
                "sha256_cert_fingerprints": [
                    "8A:38:5A:7E:E7:0A:59:2D:5D:69:98:FA:5C:FE:5D:C9:69:EE:86:41:9C:3F:B1:7C:23:41:BB:4F:06:29:A6:BF"
                ]
            }
        }
    ], safe=False)


urlpatterns = [
    path('.well-known/assetlinks.json', assetlinks_view),
    path('k/<str:invite_code>/', KhatmWebPreviewView.as_view(), name='khatm-short-link'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/notes/', include('apps.notes.urls')),
    path('api/bot/', include('apps.notes.bot_urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/donations/', include('apps.donations.urls')),
    path('api/donations/', include('apps.donations.urls')),
    path('api/v1/marketplace/', include('apps.marketplace.urls')),
    path('api/plugins/quran/', include('plugins.quran.urls')),
    path('api/plugins/', include('apps.plugin_system.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
    path('', include('apps.ota.urls')),
    path('api/v1/subscriptions/', include('apps.subscriptions.urls')),
    
    # سرو فایل‌های آپلود شده بدون وابستگی به DEBUG
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]