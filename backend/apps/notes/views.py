from django.db.models import Q, Count
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Topic, Post, PostReaction, PostComment
from .serializers import TopicSerializer, PostSerializer, PostCommentSerializer
from .services import create_bot_tasks


class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer

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
        if instance.created_by != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied("شما اجازه ویرایش این تاپیک را ندارید.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.created_by != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied("شما اجازه حذف این تاپیک را ندارید.")
        instance.delete()


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer

    def get_queryset(self):
        queryset = Post.objects.select_related('author', 'topic').all().order_by('-created_at')
        topic_id = self.request.query_params.get('topic')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'react']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)
        
        # همگام‌سازی و ساخت تسک‌های ربات
        create_bot_tasks(post, old_instance=None)
        
        # به‌روزرسانی دیسکریپشن تاپیک به عنوان خلاصه آخرین پست
        topic = post.topic
        snippet = post.content[:150] + "..." if len(post.content) > 150 else post.content
        topic.description = snippet
        topic.save()

    def perform_update(self, serializer):
        old_post = self.get_object()
        if old_post.author != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied("شما اجازه ویرایش این پست را ندارید.")
        
        post = serializer.save()
        create_bot_tasks(post, old_instance=old_post)

        # به‌روزرسانی خلاصه تاپیک در صورت نیاز
        topic = post.topic
        snippet = post.content[:150] + "..." if len(post.content) > 150 else post.content
        topic.description = snippet
        topic.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied("شما اجازه حذف این پست را ندارید.")
        
        create_bot_tasks(instance, is_delete=True)
        instance.delete()

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
