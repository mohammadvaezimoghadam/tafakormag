# apps/ota/urls.py
from django.urls import path, re_path
from .views import (
    OtaCheckV1APIView,
    OtaReportV1APIView,
    OtaPublishV1APIView,
    DashboardView,
    StatusAPIView,
    AppsAPIView,
    UpdateAppAPIView,
    DeleteAppAPIView,
    PatchesAPIView,
    UploadPatchAPIView,
    ActivatePatchAPIView,
    ToggleForceAPIView,
    DeletePatchAPIView,
    CheckUpdateAPIView,
    DownloadPatchView,
    DownloadReleaseView,
    ReleasesAPIView,
    UploadReleaseAPIView,
    ActivateReleaseAPIView,
    ToggleForceReleaseAPIView,
    DeleteReleaseAPIView,
)

app_name = 'ota'

urlpatterns = [
    # صفحات وب داشبورد
    path('', DashboardView.as_view(), name='dashboard'),
    path('ota/', DashboardView.as_view(), name='dashboard_ota'),
    path('ota/dashboard', DashboardView.as_view(), name='dashboard_ota_tab'),
    path('dashboard', DashboardView.as_view(), name='dashboard_tab'),
    path('publisher', DashboardView.as_view(), name='publisher_tab'),
    path('rollback', DashboardView.as_view(), name='rollback_tab'),
    path('apps', DashboardView.as_view(), name='apps_tab'),

    # اندپوینت‌های وضعیت سرور (هم بدون پیشوند و هم با پیشوند ota)
    path('api/status', StatusAPIView.as_view(), name='api_status'),
    path('ota/api/status', StatusAPIView.as_view(), name='api_status_ota'),
    path('status', StatusAPIView.as_view(), name='status'),

    # اندپوینت‌های کلاینت فلاتر
    path('api/v1/ota/check/', OtaCheckV1APIView.as_view(), name='api_v1_ota_check'),
    path('ota/api/v1/ota/check/', OtaCheckV1APIView.as_view(), name='api_v1_ota_check_ota'),
    path('api/v1/ota/report/', OtaReportV1APIView.as_view(), name='api_v1_ota_report'),
    path('ota/api/v1/ota/report/', OtaReportV1APIView.as_view(), name='api_v1_ota_report_ota'),
    path('api/v1/ota/publish/', OtaPublishV1APIView.as_view(), name='api_v1_ota_publish'),
    path('ota/api/v1/ota/publish/', OtaPublishV1APIView.as_view(), name='api_v1_ota_publish_ota'),
    path('check', CheckUpdateAPIView.as_view(), name='check_update'),
    re_path(r'^patches/(?P<rel_path>.*)$', DownloadPatchView.as_view(), name='download_patch'),
    re_path(r'^releases/(?P<rel_path>.*)$', DownloadReleaseView.as_view(), name='download_release'),

    # اندپوینت‌های REST API برنامه‌ها
    path('api/apps', AppsAPIView.as_view(), name='api_apps'),
    path('ota/api/apps', AppsAPIView.as_view(), name='api_apps_ota'),
    path('api/apps/update', UpdateAppAPIView.as_view(), name='api_update_app'),
    path('ota/api/apps/update', UpdateAppAPIView.as_view(), name='api_update_app_ota'),
    path('api/apps/delete', DeleteAppAPIView.as_view(), name='api_delete_app'),
    path('ota/api/apps/delete', DeleteAppAPIView.as_view(), name='api_delete_app_ota'),
    path('api/patches', PatchesAPIView.as_view(), name='api_patches'),
    path('ota/api/patches', PatchesAPIView.as_view(), name='api_patches_ota'),
    path('api/patches/upload', UploadPatchAPIView.as_view(), name='api_upload_patch'),
    path('ota/api/patches/upload', UploadPatchAPIView.as_view(), name='api_upload_patch_ota'),
    path('api/patches/activate', ActivatePatchAPIView.as_view(), name='api_activate_patch'),
    path('ota/api/patches/activate', ActivatePatchAPIView.as_view(), name='api_activate_patch_ota'),
    path('api/patches/toggle_force', ToggleForceAPIView.as_view(), name='api_toggle_force'),
    path('ota/api/patches/toggle_force', ToggleForceAPIView.as_view(), name='api_toggle_force_ota'),
    path('api/patches/delete', DeletePatchAPIView.as_view(), name='api_delete_patch'),
    path('ota/api/patches/delete', DeletePatchAPIView.as_view(), name='api_delete_patch_ota'),

    # اندپوینت‌های REST API ریلیزهای نیتیو APK
    path('api/releases', ReleasesAPIView.as_view(), name='api_releases'),
    path('ota/api/releases', ReleasesAPIView.as_view(), name='api_releases_ota'),
    path('api/releases/upload', UploadReleaseAPIView.as_view(), name='api_upload_release'),
    path('ota/api/releases/upload', UploadReleaseAPIView.as_view(), name='api_upload_release_ota'),
    path('api/releases/activate', ActivateReleaseAPIView.as_view(), name='api_activate_release'),
    path('ota/api/releases/activate', ActivateReleaseAPIView.as_view(), name='api_activate_release_ota'),
    path('api/releases/toggle_force', ToggleForceReleaseAPIView.as_view(), name='api_toggle_force_release'),
    path('ota/api/releases/toggle_force', ToggleForceReleaseAPIView.as_view(), name='api_toggle_force_release_ota'),
    path('api/releases/delete', DeleteReleaseAPIView.as_view(), name='api_delete_release'),
    path('ota/api/releases/delete', DeleteReleaseAPIView.as_view(), name='api_delete_release_ota'),
]
