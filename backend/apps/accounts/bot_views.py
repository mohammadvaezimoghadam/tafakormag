from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from apps.notes.bot_permissions import IsBotService

from .models import MessagingTarget, User


def _valid_platform(platform):
    return platform in ("telegram", "bale")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([IsBotService])
def register_destination(request):
    user_id = request.data.get("user_id")
    platform = request.data.get("platform")
    chat_id = request.data.get("chat_id")
    label = request.data.get("label")

    if not user_id or not _valid_platform(platform) or not chat_id or not label:
        return Response(
            {"error": "user_id, platform, chat_id and label are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    has_default = MessagingTarget.objects.filter(
        user=user, platform=platform, is_default=True
    ).exists()

    try:
        target = MessagingTarget.objects.create(
            user=user,
            platform=platform,
            chat_id=str(chat_id),
            label=label,
            is_default=not has_default,
        )
    except IntegrityError:
        return Response(
            {"error": "Destination already registered for this user and platform"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "id": target.id,
            "chat_id": target.chat_id,
            "label": target.label,
            "is_default": target.is_default,
            "is_active": target.is_active,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([IsBotService])
def list_destinations(request):
    user_id = request.query_params.get("user_id")
    platform = request.query_params.get("platform")

    if not user_id or not _valid_platform(platform):
        return Response(
            {"error": "user_id and platform are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    targets = MessagingTarget.objects.filter(user_id=user_id, platform=platform)
    data = [
        {
            "id": t.id,
            "chat_id": t.chat_id,
            "label": t.label,
            "is_default": t.is_default,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat(),
        }
        for t in targets
    ]
    return Response(data)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([IsBotService])
def set_default_destination(request):
    user_id = request.data.get("user_id")
    platform = request.data.get("platform")
    destination_id = request.data.get("destination_id")

    if not user_id or not _valid_platform(platform) or not destination_id:
        return Response(
            {"error": "user_id, platform and destination_id are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    target = MessagingTarget.objects.filter(
        pk=destination_id,
        user_id=user_id,
        platform=platform,
    ).first()
    if target is None:
        return Response(
            {"error": "Destination not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # اول وضعیت پیش‌فرض همه مقاصد دیگر کاربر روی این پلتفرم غیرفعال شود
    MessagingTarget.objects.filter(
        user_id=user_id,
        platform=platform,
    ).update(is_default=False)

    target.is_default = True
    target.save()
    return Response({"success": True})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([IsBotService])
def delete_destination(request):
    user_id = request.data.get("user_id")
    platform = request.data.get("platform")
    destination_id = request.data.get("destination_id")

    if not user_id or not _valid_platform(platform) or not destination_id:
        return Response(
            {"error": "user_id, platform and destination_id are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    target = MessagingTarget.objects.filter(
        pk=destination_id,
        user_id=user_id,
        platform=platform,
    ).first()
    if target is None:
        return Response(
            {"error": "Destination not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    was_default = target.is_default
    target.delete()

    # اگر مقصد حذف شده پیش‌فرض بود، مقصد بعدی (در صورت وجود) پیش‌فرض شود
    if was_default:
        next_target = MessagingTarget.objects.filter(
            user_id=user_id, platform=platform
        ).first()
        if next_target:
            next_target.is_default = True
            next_target.save()

    return Response({"success": True})


@api_view(["GET"])
@authentication_classes([])
@permission_classes([IsBotService])
def user_by_chat(request):
    platform = request.query_params.get("platform")
    chat_id = request.query_params.get("chat_id")

    if not _valid_platform(platform) or chat_id in (None, ""):
        return Response(
            {"error": "platform and chat_id are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    field = f"{platform}_chat_id"
    user = User.objects.filter(**{field: str(chat_id)}).first()
    if user is None:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response({"user_id": user.id})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([IsBotService])
def register_phone_chat(request):
    phone = request.data.get("phone")
    platform = request.data.get("platform")
    chat_id = request.data.get("chat_id")

    if not phone or not _valid_platform(platform) or chat_id in (None, ""):
        return Response(
            {"error": "phone, platform and chat_id are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    phone = str(phone).strip()
    if phone.startswith("+98"):
        phone = "0" + phone[3:]
    elif phone.startswith("98"):
        phone = "0" + phone[2:]

    user, created = User.objects.get_or_create(phone=phone)
    field = f"{platform}_chat_id"
    setattr(user, field, str(chat_id))
    user.save()

    return Response({"success": True, "created": created})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([IsBotService])
def toggle_active_destination(request):
    user_id = request.data.get("user_id")
    platform = request.data.get("platform")
    destination_id = request.data.get("destination_id")

    if not user_id or not _valid_platform(platform) or not destination_id:
        return Response(
            {"error": "user_id, platform and destination_id are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    target = MessagingTarget.objects.filter(
        pk=destination_id,
        user_id=user_id,
        platform=platform,
    ).first()
    if target is None:
        return Response(
            {"error": "Destination not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    target.is_active = not target.is_active
    target.save()
    return Response({"success": True, "is_active": target.is_active})
