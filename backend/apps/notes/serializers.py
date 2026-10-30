from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Topic, Post, PostReaction, PostComment, ImportTask, TopicAdmin
from apps.accounts.models import MessagingTarget
from apps.plugin_system.models import Plugin, PostPluginReference
from apps.plugin_system.validator import PluginReferenceValidator

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
            'id', 'name', 'image', 'description', 'post_badge', 'created_by', 'created_by_phone',
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


class PostPluginReferenceSerializer(serializers.ModelSerializer):
    plugin = serializers.CharField(required=False, write_only=True)
    plugin_identifier = serializers.CharField(source='plugin.identifier', read_only=True)

    class Meta:
        model = PostPluginReference
        fields = [
            'id', 'plugin', 'plugin_identifier', 'resource_type',
            'external_id', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'plugin_identifier', 'created_at']

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        raw_plugin = data.get('plugin') or data.get('plugin_identifier') or 'quran'

        if isinstance(raw_plugin, str) and len(raw_plugin) == 36 and '-' in raw_plugin:
            plugin_obj = Plugin.objects.filter(Q(identifier=raw_plugin) | Q(id=raw_plugin)).first()
        else:
            plugin_obj = Plugin.objects.filter(identifier=str(raw_plugin)).first()

        if not plugin_obj:
            plugin_obj = Plugin.objects.filter(identifier='quran').first()
            if not plugin_obj:
                raise serializers.ValidationError({'plugin': f"پلاگین با شناسه '{raw_plugin}' یافت نشد."})

        ret['plugin'] = plugin_obj

        res_type = ret.get('resource_type', '')
        ext_id = ret.get('external_id', '')
        try:
            canonical_id, default_meta = PluginReferenceValidator.normalize_and_validate(
                plugin_obj.identifier, res_type, ext_id
            )
            ret['external_id'] = canonical_id
            meta = ret.get('metadata') or {}
            for k, v in default_meta.items():
                meta.setdefault(k, v)
            ret['metadata'] = meta
        except ValueError as e:
            raise serializers.ValidationError({'external_id': str(e)})

        return ret


class PostSerializer(serializers.ModelSerializer):
    author_phone = serializers.SerializerMethodField(read_only=True)
    author_name = serializers.SerializerMethodField(read_only=True)
    author_avatar = serializers.SerializerMethodField(read_only=True)
    reactions_summary = serializers.SerializerMethodField(read_only=True)
    user_reaction = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)
    donation_campaign = serializers.SerializerMethodField(read_only=True)
    plugin_references = PostPluginReferenceSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = [
            'id', 'topic', 'author', 'author_phone', 'author_name', 'author_avatar', 'content',
            'media_type', 'media_file', 'created_at', 'updated_at',
            'reactions_summary', 'user_reaction', 'comments_count',
            'telegram_message_ids', 'bale_message_ids',
            'content_hash', 'published_platforms', 'donation_campaign',
            'plugin_references'
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at', 'telegram_message_ids', 'bale_message_ids',
            'content_hash', 'published_platforms', 'donation_campaign'
        ]

    def create(self, validated_data):
        plugin_references_data = validated_data.pop('plugin_references', [])
        post = super().create(validated_data)
        for ref_data in plugin_references_data:
            plugin = ref_data.pop('plugin')
            PostPluginReference.objects.get_or_create(post=post, plugin=plugin, **ref_data)
        return post

    def update(self, instance, validated_data):
        plugin_references_data = validated_data.pop('plugin_references', None)
        post = super().update(instance, validated_data)
        if plugin_references_data is not None:
            instance.plugin_references.all().delete()
            for ref_data in plugin_references_data:
                plugin = ref_data.pop('plugin')
                PostPluginReference.objects.get_or_create(post=post, plugin=plugin, **ref_data)
        return post

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


class ImportTaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportTask
        fields = [
            'id', 'topic', 'status', 'current_stage', 'progress',
            'error_message', 'created_at'
        ]
        read_only_fields = fields
