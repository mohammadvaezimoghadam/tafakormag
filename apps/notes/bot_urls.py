from django.urls import path

from apps.accounts import bot_views as accounts_bot_views

from . import bot_views

urlpatterns = [
    path("verify-link/", bot_views.verify_link, name="bot-verify-link"),
    path("tasks/", bot_views.fetch_tasks, name="bot-fetch-tasks"),
    path("tasks/<int:task_id>/", bot_views.complete_task, name="bot-complete-task"),
    path(
        "register-destination/",
        accounts_bot_views.register_destination,
        name="bot-register-destination",
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
        "user-by-chat/",
        accounts_bot_views.user_by_chat,
        name="bot-user-by-chat",
    ),
]
