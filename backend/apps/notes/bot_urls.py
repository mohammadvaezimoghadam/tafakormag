from django.urls import path

from apps.accounts import bot_views as accounts_bot_views

from . import bot_views

urlpatterns = [
    path("verify-link/", bot_views.verify_link, name="bot-verify-link"),
    path("tasks/", bot_views.fetch_tasks, name="bot-fetch-tasks"),
    path("tasks/<int:task_id>/", bot_views.task_detail_view, name="bot-task-detail"),
    path("tasks/<int:task_id>/retry/", bot_views.retry_task, name="bot-retry-task"),
    path(
        "register-destination/",
        accounts_bot_views.register_destination,
        name="bot-register-destination",
    ),
    path(
        "register-phone-chat/",
        accounts_bot_views.register_phone_chat,
        name="bot-register-phone-chat",
    ),
    path(
        "destinations/",
        accounts_bot_views.list_destinations,
        name="bot-list-destinations",
    ),
    path(
        "set-default-destination/",
        accounts_bot_views.set_default_destination,
        name="bot-set-default-destination",
    ),
    path(
        "delete-destination/",
        accounts_bot_views.delete_destination,
        name="bot-delete-destination",
    ),
    path(
        "toggle-active-destination/",
        accounts_bot_views.toggle_active_destination,
        name="bot-toggle-active-destination",
    ),
    path(
        "user-by-chat/",
        accounts_bot_views.user_by_chat,
        name="bot-user-by-chat",
    ),
    path(
        "unregister-chat/",
        accounts_bot_views.unregister_chat,
        name="bot-unregister-chat",
    ),
    path(
        "report-bot-disconnect/",
        accounts_bot_views.report_bot_disconnect,
        name="bot-report-disconnect",
    ),
]
