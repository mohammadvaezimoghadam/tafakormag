from rest_framework import serializers
from .models import Topic, Post, PostReaction, PostComment
from apps.accounts.models import MessagingTarget


class TopicSerializer(serializers.ModelSerializer):
    created_by_phone = serializers.SerializerMethodField(read_only=True)
    post_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Topic
        fields = [
            'id', 'name', 'image', 'description', 'created_by', 'created_by_phone',
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
        fields = ['id', 'post', 'user', 'user_phone', 'user_name', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_user_phone(self, obj):
        return obj.user.phone

    def get_user_name(self, obj):
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

    class Meta:
        model = Post
        fields = [
            'id', 'topic', 'author', 'author_phone', 'author_name', 'author_avatar', 'content',
            'media_type', 'media_file', 'created_at', 'updated_at',
            'reactions_summary', 'user_reaction', 'comments_count',
            'telegram_message_ids', 'bale_message_ids'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'telegram_message_ids', 'bale_message_ids']

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