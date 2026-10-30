import os
from django.db.models import Q, Count
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from apps.accounts.models import User
from .models import Topic, Post, PostReaction, PostComment, ImportTask, TopicAdmin
from .serializers import (
    TopicSerializer, PostSerializer, PostCommentSerializer, ImportTaskStatusSerializer,
    TopicAdminSerializer, UserSimpleSerializer
)
from .permissions import IsTopicOwnerOrAdmin
from .services import create_bot_tasks, execute_external_platform_deletion, check_duplicate_message


def update_topic_description(topic):
    latest_post = topic.posts.all().order_by('-created_at').first()
    if latest_post:
        snippet = latest_post.content[:150] + "..." if len(latest_post.content) > 150 else latest_post.content
        topic.description = snippet
    else:
        topic.description = ""
    topic.save()


class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    permission_classes = [IsTopicOwnerOrAdmin]

    def get_queryset(self):
        # شمارش پست‌ها برای هر تاپیک و مرتب‌سازی بر اساس آخرین تاپیک‌های ایجاد شده
        return Topic.objects.annotate(post_count=Count('posts')).order_by('-created_at')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        is_owner = (instance.created_by == self.request.user) if instance.created_by else False
        is_admin = instance.admins.filter(user=self.request.user).exists()
        if not (is_owner or is_admin or self.request.user.is_superuser):
            raise PermissionDenied("شما اجازه ویرایش این تاپیک را ندارید.")
        serializer.save()

    def perform_destroy(self, instance):
        is_owner = (instance.created_by == self.request.user) if instance.created_by else False
        if not (is_owner or self.request.user.is_superuser):
            raise PermissionDenied("فقط سازنده تاپیک مجاز به حذف آن است.")
        
        # پاکسازی صریح پویش‌های اهدا و تراکنش‌های مربوطه قبل از حذف تاپیک
        try:
            from apps.donations.models import DonationCampaign, DonationTransaction
            campaign_ids = list(instance.donation_campaigns.values_list('id', flat=True))
            if campaign_ids:
                DonationTransaction.objects.filter(campaign_id__in=campaign_ids).delete()
                instance.donation_campaigns.all().delete()
        except Exception:
            pass

        instance.delete()

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def admins(self, request, pk=None):
        """
        GET /api/topics/{id}/admins/
        Public endpoint: Returns the Topic Owner details along with a list of active Admins.
        """
        topic = self.get_object()
        admins = topic.admins.select_related('user', 'promoted_by').all()
        admin_serializer = TopicAdminSerializer(admins, many=True)

        owner_data = UserSimpleSerializer(topic.created_by).data if topic.created_by else None

        return Response({
            "owner": owner_data,
            "admins": admin_serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='add_admin', permission_classes=[permissions.IsAuthenticated])
    def add_admin(self, request, pk=None):
        """
        POST /api/topics/{id}/add_admin/
        Restricted to Topic Owner only: Grants admin access to a specified user.
        Payload: { "user_id": "<uuid_or_id>", "custom_title": "Moderator" }
        """
        topic = self.get_object()

        if topic.created_by != request.user and not request.user.is_superuser:
            return Response(
                {"error": "Only the topic owner can appoint new administrators."},
                status=status.HTTP_403_FORBIDDEN
            )

        target_user_id = str(request.data.get('user_id', '')).strip()
        custom_title = request.data.get('custom_title', 'Admin')

        if not target_user_id:
            return Response(
                {"error": "وارد کردن شناسه کاربر یا شماره موبایل الزامی است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # جستجو بر اساس ID یا شماره موبایل
        user_query = User.objects.filter(Q(id=target_user_id) | Q(phone=target_user_id)) if target_user_id.isdigit() else User.objects.filter(phone=target_user_id)
        target_user = user_query.first()

        if not target_user:
            return Response(
                {"error": "کاربری با این شناسه یا شماره موبایل یافت نشد."},
                status=status.HTTP_404_NOT_FOUND
            )

        if topic.created_by and topic.created_by == target_user:
            return Response(
                {"error": "سازنده تاپیک مالک اصلی است و نمی‌تواند به عنوان ادمین مجدد ثبت شود."},
                status=status.HTTP_400_BAD_REQUEST
            )

        topic_admin, created = TopicAdmin.objects.get_or_create(
            topic=topic,
            user=target_user,
            defaults={
                'promoted_by': request.user,
                'custom_title': customTitle if (customTitle := str(custom_title).strip()) else 'Admin'
            }
        )

        if not created:
            return Response(
                {"error": "این کاربر از قبل ادمین این تاپیک می‌باشد."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TopicAdminSerializer(topic_admin)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'remove_admin/(?P<user_id>[^/]+)', permission_classes=[permissions.IsAuthenticated])
    def remove_admin(self, request, pk=None, user_id=None):
        """
        DELETE /api/topics/{id}/remove_admin/{user_id}/
        Restricted to Topic Owner only: Revokes administrator rights from a user.
        """
        topic = self.get_object()

        if topic.created_by != request.user and not request.user.is_superuser:
            return Response(
                {"error": "فقط سازنده تاپیک مجاز به حذف ادمین‌ها است."},
                status=status.HTTP_403_FORBIDDEN
            )

        admin_record = TopicAdmin.objects.filter(
            Q(topic=topic) & (Q(user_id=user_id) | Q(user__phone=user_id))
        ).first()

        if admin_record:
            admin_record.delete()
            return Response({"message": "دسترسی ادمین با موفقیت حذف شد."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "کاربر مورد نظر در لیست ادمین‌های این تاپیک یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='transfer_ownership', permission_classes=[permissions.IsAuthenticated])
    def transfer_ownership(self, request, pk=None):
        """
        POST /api/topics/{id}/transfer_ownership/
        Restricted to Topic Owner only: Transfers topic ownership to another user.
        Payload: { "new_owner_id": "<user_id_or_phone>" }
        """
        topic = self.get_object()

        if topic.created_by != request.user and not request.user.is_superuser:
            return Response(
                {"error": "فقط سازنده فعلی تاپیک مجاز به انتقال مالکیت است."},
                status=status.HTTP_403_FORBIDDEN
            )

        new_owner_id = str(request.data.get('new_owner_id', '')).strip()

        if not new_owner_id:
            return Response(
                {"error": "وارد کردن شناسه مالک جدید یا شماره موبایل الزامی است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_query = User.objects.filter(Q(id=new_owner_id) | Q(phone=new_owner_id)) if new_owner_id.isdigit() else User.objects.filter(phone=new_owner_id)
        new_owner = user_query.first()

        if not new_owner:
            return Response(
                {"error": "کاربری با این شناسه یا شماره موبایل یافت نشد."},
                status=status.HTTP_404_NOT_FOUND
            )

        if topic.created_by == new_owner:
            return Response(
                {"error": "شما در حال حاضر مالک این تاپیک هستید."},
                status=status.HTTP_400_BAD_REQUEST
            )

        previous_owner = topic.created_by

        # حذف از لیست ادمین‌ها در صورت وجود
        TopicAdmin.objects.filter(topic=topic, user=new_owner).delete()

        # انتقال مالکیت
        topic.created_by = new_owner
        topic.save()

        # تبدیل مالک قبلی به ادمین تاپیک جهت حفظ دسترسی دست‌اندرکاران
        if previous_owner:
            TopicAdmin.objects.get_or_create(
                topic=topic,
                user=previous_owner,
                defaults={
                    'promoted_by': new_owner,
                    'custom_title': 'مالک قبلی'
                }
            )

        owner_data = UserSimpleSerializer(new_owner).data
        return Response({
            "message": "مالکیت تاپیک با موفقیت منتقل شد.",
            "owner": owner_data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='import-json', permission_classes=[permissions.IsAuthenticated])
    def import_json(self, request, pk=None):
        topic = self.get_object()
        
        # بررسی دسترسی سازنده تاپیک
        if topic.created_by and topic.created_by != request.user and not request.user.is_superuser:
            raise PermissionDenied("فقط سازنده تاپیک مجاز به درون‌ریزی تاریخچه در آن است.")
            
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({"error": "هیچ فایلی ارسال نشده است."}, status=status.HTTP_400_BAD_REQUEST)
        
        filename_lower = uploaded_file.name.lower()
        
        # تشخیص نوع فایل برای routing به handler مناسب
        if filename_lower.endswith('.json'):
            file_type = 'json'
        elif filename_lower.endswith('.zip'):
            file_type = 'zip'
        else:
            return Response(
                {"error": "فرمت فایل پشتیبانی نمی‌شود. فقط فایل‌های .json یا .zip مجاز هستند."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # ذخیره فایل به صورت موقت در media/temp_imports/
            import uuid
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_imports')
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
            temp_filepath = os.path.join(temp_dir, temp_filename)
            
            # نوشتن فایل روی دیسک
            with open(temp_filepath, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
        except Exception as e:
            return Response({"error": f"خطا در ذخیره‌سازی فایل موقت: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
                
        # ایجاد تسک وضعیت درون‌ریزی
        task = ImportTask.objects.create(
            topic=topic,
            status='PENDING',
            current_stage='در حال شروع فرآیند درون‌ریزی...',
            progress=0
        )
        
        # اجرای ناهمگام تسک در پس‌زمینه بر اساس نوع فایل
        import threading
        
        if file_type == 'zip':
            from .services import process_telegram_zip_import
            target_func = process_telegram_zip_import
        else:
            from .services import process_telegram_json_import
            target_func = process_telegram_json_import
        
        thread = threading.Thread(
            target=target_func,
            args=(str(task.id), temp_filepath)
        )
        thread.daemon = True
        thread.start()
        
        # بازگرداندن پاسخ ۲۰۲ Accepted به همراه شناسه تسک
        serializer = ImportTaskStatusSerializer(task)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Post.objects.select_related('author', 'topic').prefetch_related('plugin_references__plugin').all().order_by('-created_at')
        topic_id = self.request.query_params.get('topic_id') or self.request.query_params.get('topic')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        ayah = self.request.query_params.get('ayah')
        if ayah:
            if ':' in ayah and not ayah.startswith('surah:'):
                parts = ayah.split(':')
                canonical = f"surah:{parts[0]},ayah:{parts[1]}"
            else:
                canonical = ayah
            queryset = queryset.filter(
                plugin_references__resource_type='ayah',
                plugin_references__external_id=canonical
            ).distinct()

        external_id = self.request.query_params.get('external_id')
        if external_id:
            queryset = queryset.filter(plugin_references__external_id=external_id).distinct()

        plugin = self.request.query_params.get('plugin')
        if plugin:
            queryset = queryset.filter(plugin_references__plugin__identifier=plugin).distinct()

        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'react', 'selective_delete', 'check_duplicate']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        topic = serializer.validated_data.get('topic')
        if topic:
            is_owner = (topic.created_by == self.request.user) if topic.created_by else False
            is_admin = topic.admins.filter(user=self.request.user).exists()
            if not (is_owner or is_admin or self.request.user.is_superuser):
                raise PermissionDenied("فقط سازنده تاپیک و ادمین‌های آن مجاز به ارسال پیام در آن هستند.")

        # الصاق خودکار امضای منبع (بج تاپیک) به انتهای متن پست در صورت وجود
        content = (serializer.validated_data.get('content', '') or "").strip()
        if topic and getattr(topic, 'post_badge', ''):
            badge = topic.post_badge.strip()
            if badge and badge not in content:
                content = f"{content}\n\n{badge}" if content else badge
                serializer.validated_data['content'] = content

        post = serializer.save(author=self.request.user)
        
        # همگام‌سازی و ساخت تسک‌های ربات
        create_bot_tasks(post, old_instance=None)
        
        # به‌روزرسانی خلاصه تاپیک
        update_topic_description(post.topic)

    def perform_update(self, serializer):
        old_post = self.get_object()
        topic = old_post.topic
        is_owner = (topic.created_by == self.request.user) if topic and topic.created_by else False
        is_admin = topic.admins.filter(user=self.request.user).exists() if topic else False
        is_author = (old_post.author == self.request.user)
        if not (is_author or is_owner or is_admin or self.request.user.is_superuser):
            raise PermissionDenied("شما اجازه ویرایش این پست را ندارید.")
        
        post = serializer.save()
        create_bot_tasks(post, old_instance=old_post)

        # به‌روزرسانی خلاصه تاپیک
        update_topic_description(post.topic)

    def perform_destroy(self, instance):
        topic = instance.topic
        is_owner = (topic.created_by == self.request.user) if topic and topic.created_by else False
        is_admin = topic.admins.filter(user=self.request.user).exists() if topic else False
        is_author = (instance.author == self.request.user)
        if not (is_author or is_owner or is_admin or self.request.user.is_superuser):
            raise PermissionDenied("شما اجازه حذف این پست را ندارید.")
        
        create_bot_tasks(instance, is_delete=True)
        instance.delete()
        
        # به‌روزرسانی خلاصه تاپیک پس از حذف
        update_topic_description(topic)


    @action(methods=['get'], detail=False, url_path='search')
    def search(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "پارامتر q الزامی است."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(content__icontains=query)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # اندپوینت ثبت واکنش روی پست
    @action(methods=['post'], detail=True, url_path='react')
    def react(self, request, pk=None):
        post = self.get_object()
        emoji = request.data.get('emoji', '').strip()
        
        # لیست ایموجی‌های مجاز طبق نظر کاربر
        # لایک (👍)، دیسلایک (👎)، قلب (❤️)، خنده (😂)، شادی (🎉)
        allowed_emojis = ["👍", "👎", "❤️", "😂", "🎉"]
        
        if not emoji:
            # اگر ایموجی خالی بود، واکنش قبلی کاربر را حذف می‌کنیم
            PostReaction.objects.filter(post=post, user=request.user).delete()
            return Response({"success": True, "message": "واکنش حذف شد."})

        if emoji not in allowed_emojis:
            return Response(
                {"error": "ایموجی ارسالی مجاز نیست. ایموجی‌های مجاز: 👍، 👎، ❤️، 😂، 🎉"},
                status=status.HTTP_400_BAD_REQUEST
            )

        reaction, created = PostReaction.objects.update_or_create(
            post=post,
            user=request.user,
            defaults={'emoji': emoji}
        )
        return Response({"success": True, "emoji": emoji, "created": created})

    # اندپوینت کامنت‌های پست (مشاهده و ثبت)
    @action(methods=['get', 'post'], detail=True, url_path='comments')
    def comments(self, request, pk=None):
        post = self.get_object()
        
        if request.method == 'GET':
            comments = post.comments.select_related('user').all()
            serializer = PostCommentSerializer(comments, many=True)
            return Response(serializer.data)
        
        # درخواست POST نیازمند ورود کاربر است
        if not request.user.is_authenticated:
            return Response(
                {"detail": "برای ثبت نظر ابتدا باید وارد حساب خود شوید."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        content = request.data.get('content', '').strip()
        if not content:
            return Response({"error": "متن نظر نمی‌تواند خالی باشد."}, status=status.HTTP_400_BAD_REQUEST)

        comment = PostComment.objects.create(
            post=post,
            user=request.user,
            content=content
        )
        serializer = PostCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='selective-delete')
    def selective_delete(self, request, pk=None):
        post = self.get_object()
        
        delete_telegram = request.data.get('delete_from_telegram', False)
        delete_bale = request.data.get('delete_from_bale', False)
        delete_db = request.data.get('delete_from_db', False)

        # Validation Guard
        has_tg = bool(post.telegram_message_ids) or "telegram" in (post.published_platforms or [])
        if delete_telegram and not has_tg:
            return Response({"error": "Post is not published on Telegram."}, status=status.HTTP_400_BAD_REQUEST)
            
        has_bale = bool(post.bale_message_ids) or "bale" in (post.published_platforms or [])
        if delete_bale and not has_bale:
            return Response({"error": "Post is not published on Bale."}, status=status.HTTP_400_BAD_REQUEST)

        # Offload background deletion thread
        import threading
        threading.Thread(
            target=execute_external_platform_deletion,
            args=(post.id, delete_telegram, delete_bale, delete_db),
            daemon=True
        ).start()

        return Response(
            {"message": "Deletion request accepted."}, 
            status=status.HTTP_202_ACCEPTED
        )

    @action(detail=False, methods=['post'], url_path='check-duplicate')
    def check_duplicate(self, request):
        topic_id = request.data.get('topic_id') or request.data.get('topic')
        content = request.data.get('content', '')
        
        if not topic_id:
            return Response({"error": "Field 'topic_id' or 'topic' is required."}, status=status.HTTP_400_BAD_REQUEST)

        temp_post = Post(content=content)
        content_hash = temp_post.compute_content_hash()

        is_dup, existing_post = check_duplicate_message(topic_id, content_hash)

        if is_dup and existing_post:
            return Response({
                "is_duplicate": True,
                "existing_post_id": existing_post.id,
                "created_at": existing_post.created_at,
                "published_platforms": existing_post.published_platforms
            }, status=status.HTTP_200_OK)

        return Response({"is_duplicate": False}, status=status.HTTP_200_OK)


class ImportTaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ImportTask.objects.all()
    serializer_class = ImportTaskStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return ImportTask.objects.all()
        return ImportTask.objects.filter(topic__created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        task = self.get_object()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
