import uuid

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from apps.accounts.models import BotConnectionToken, User

from .bot_permissions import IsBotService
from .models import BotTask, Post
from .services import get_message_ids, set_message_ids


@api_view(["POST"])
@authentication_classes([])
@permission_classes([IsBotService])
def verify_link(request):
    token_str = request.data.get("token")
    platform = request.data.get("platform")
    chat_id = request.data.get("chat_id")

    if platform not in ("telegram", "bale") or not token_str or chat_id in (None, ""):
        return Response(
            {"error": "Invalid or expired token"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        token_uuid = uuid.UUID(str(token_str))
    except ValueError:
        return Response(
            {"error": "Invalid or expired token"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    conn = (
        BotConnectionToken.objects.filter(
            token=token_uuid, platform=platform, is_used=False
        )
        .select_related("user")
        .first()
    )

    if conn is None or not conn.is_valid():
        return Response(
            {"error": "Invalid or expired token"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = conn.user
    field = f"{platform}_chat_id"
    User.objects.filter(pk=user.pk).update(**{field: str(chat_id)})
    BotConnectionToken.objects.filter(pk=conn.pk).update(is_used=True)

    return Response({"success": True})


@api_view(["GET"])
@authentication_classes([])
@permission_classes([IsBotService])
def fetch_tasks(request):
    tasks = BotTask.objects.filter(processed=False).order_by("created_at")
    data = []
    for t in tasks:
        bot_token = t.bot_token
        media_type = "text"
        media_url = None
        
        post = None
        if t.post_id:
            post = t.post_id
        elif t.note_id:
            try:
                post = Post.objects.select_related('author').get(pk=t.note_id)
            except Post.DoesNotExist:
                pass

        if post:
            if not bot_token:
                if t.platform == "telegram":
                    bot_token = post.author.telegram_bot_token
                elif t.platform == "bale":
                    bot_token = post.author.bale_bot_token
            
            media_type = post.media_type
            if post.media_file:
                media_url = request.build_absolute_uri(post.media_file.url)

        data.append({
            "id": t.id,
            "action": t.action,
            "platform": t.platform,
            "chat_id": t.chat_id,
            "text": t.text,
            "message_id": t.message_id or None,
            "note_id": post.id if post else t.note_id,
            "bot_token": bot_token,
            "media_type": media_type,
            "media_url": media_url,
        })
    return Response(data)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([IsBotService])
def complete_task(request, task_id):
    task = BotTask.objects.filter(id=task_id).first()
    if task is None:
        return Response(
            {"error": "Task not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    task.processed = True
    if "message_id" in request.data and request.data.get("message_id") not in (None, ""):
        task.message_id = str(request.data["message_id"])
    task.save()

    post = None
    if task.post_id:
        post = task.post_id
    elif task.note_id:
        try:
            post = Post.objects.get(id=task.note_id)
        except Post.DoesNotExist:
            pass

    if post and task.platform in ("telegram", "bale"):
        if task.action == "send" and task.message_id:
            msg_ids = get_message_ids(post, task.platform)
            msg_ids[str(task.chat_id)] = str(task.message_id)
            set_message_ids(post, task.platform, msg_ids)
        elif task.action == "delete":
            msg_ids = get_message_ids(post, task.platform)
            if str(task.chat_id) in msg_ids:
                del msg_ids[str(task.chat_id)]
            set_message_ids(post, task.platform, msg_ids)

    return Response({"success": True})
