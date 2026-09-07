from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Topic, Post, PostReaction, PostComment, ImportTask, TopicAdmin, TopicFAQ,
    TopicChatSession, TopicChatMessage
)
from apps.accounts.models import MessagingTarget

User = get_user_model()


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'first_name', 'last_name', 'profile_image']


class TopicAdminSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    promoted_by = UserSimpleSerializer(read_only=True)

    class Meta:
        model = TopicAdmin
        fields = ['id', 'user', 'custom_title', 'promoted_by', 'created_at']




class TopicSerializer(serializers.ModelSerializer):
    created_by_phone = serializers.SerializerMethodField(read_only=True)
    post_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Topic
        fields = [
            'id', 'name', 'image', 'description', 'post_badge', 'telegram_post_badge', 'bale_post_badge',
            'telegram_post_link_mode', 'bale_post_link_mode',
            'created_by', 'created_by_phone',
            'created_at', 'telegram_bot_active', 'bale_bot_active',
            'telegram_connections', 'bale_connections', 'post_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'post_count']

    def get_created_by_phone(self, obj):
        return obj.created_by.phone if obj.created_by else None


class PostCommentSerializer(serializers.ModelSerializer):
    user_phone = serializers.SerializerMethodField(read_only=True)
    user_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PostComment
        fields = ['id', 'post', 'user', 'user_phone', 'user_name', 'content', 'is_anonymous', 'author_name', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_user_phone(self, obj):
        if obj.is_anonymous or not obj.user:
            return None
        return obj.user.phone

    def get_user_name(self, obj):
        if obj.is_anonymous or not obj.user:
            return obj.author_name.strip() if obj.author_name else "کاربر ناشناس"
        if obj.user.first_name or obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.phone


class PostReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostReaction
        fields = ['id', 'post', 'user', 'emoji', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    author_phone = serializers.SerializerMethodField(read_only=True)
    author_name = serializers.SerializerMethodField(read_only=True)
    author_avatar = serializers.SerializerMethodField(read_only=True)
    reactions_summary = serializers.SerializerMethodField(read_only=True)
    user_reaction = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)
    donation_campaign = serializers.SerializerMethodField(read_only=True)
    topic_name = serializers.SerializerMethodField(read_only=True)
    topic_image = serializers.SerializerMethodField(read_only=True)
    topic_description = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'topic', 'topic_name', 'topic_image', 'topic_description',
            'author', 'author_phone', 'author_name', 'author_avatar', 'content',
            'media_type', 'media_file', 'created_at', 'updated_at',
            'reactions_summary', 'user_reaction', 'comments_count',
            'telegram_message_ids', 'bale_message_ids',
            'content_hash', 'published_platforms', 'donation_campaign'
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at', 'telegram_message_ids', 'bale_message_ids',
            'content_hash', 'published_platforms', 'donation_campaign',
            'topic_name', 'topic_image', 'topic_description'
        ]

    def get_author_phone(self, obj):
        return obj.author.phone

    def get_author_name(self, obj):
        if obj.author.first_name or obj.author.last_name:
            return f"{obj.author.first_name} {obj.author.last_name}".strip()
        return obj.author.phone

    def get_author_avatar(self, obj):
        request = self.context.get('request')
        url = obj.author.profile_image.url if obj.author.profile_image else None
        if url and request:
            return request.build_absolute_uri(url)
        return url

    def get_reactions_summary(self, obj):
        summary = {}
        reactions = obj.reactions.all()
        for r in reactions:
            summary[r.emoji] = summary.get(r.emoji, 0) + 1
        return summary

    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            return reaction.emoji if reaction else None
        return None

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_donation_campaign(self, obj):
        campaign = getattr(obj, 'donation_campaign', None)
        if campaign:
            request = self.context.get('request')
            cover_url = campaign.cover_image.url if campaign.cover_image else None
            if cover_url and request:
                cover_url = request.build_absolute_uri(cover_url)
            return {
                'id': str(campaign.id),
                'title': campaign.title,
                'description': campaign.description,
                'category': campaign.category,
                'target_amount': campaign.target_amount,
                'collected_amount': campaign.collected_amount,
                'donors_count': campaign.donors_count,
                'status': campaign.status,
                'cover_image': cover_url,
                'deadline': campaign.deadline.isoformat() if campaign.deadline else None,
            }
        return None

    def get_topic_name(self, obj):
        return obj.topic.name if obj.topic else None

    def get_topic_image(self, obj):
        if obj.topic and obj.topic.image:
            request = self.context.get('request')
            url = obj.topic.image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

    def get_topic_description(self, obj):
        return obj.topic.description if obj.topic else None


class ImportTaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportTask
        fields = [
            'id', 'topic', 'status', 'current_stage', 'progress',
            'error_message', 'created_at'
        ]
        read_only_fields = fields


class TopicFAQSerializer(serializers.ModelSerializer):
    created_by = UserSimpleSerializer(read_only=True)
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), required=False)

    class Meta:
        model = TopicFAQ
        fields = [
            'id', 'topic', 'question', 'answer', 'order', 'is_published',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class TopicChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicChatMessage
        fields = ['id', 'session', 'role', 'content', 'sources', 'created_at']
        read_only_fields = ['id', 'session', 'role', 'sources', 'created_at']


class TopicChatSessionSerializer(serializers.ModelSerializer):
    messages = TopicChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = TopicChatSession
        fields = ['id', 'topic', 'user', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'topic', 'user', 'created_at', 'updated_at', 'messages']


class TopicChatPromptSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=3000, required=True)
    session_id = serializers.UUIDField(required=False, allow_null=True)