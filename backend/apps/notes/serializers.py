import json
from django.db.models import Q
from apps.plugin_system.models import Plugin, PostPluginReference
from apps.plugin_system.validator import PluginReferenceValidator
from rest_framework import serializers

from django.contrib.auth import get_user_model

from .models import (

    Topic, Post, PostReaction, PostComment, ImportTask, TopicAdmin, TopicFAQ,

    TopicChatSession, TopicChatMessage, PostEditProposal, PostEditHistory

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

    topic_name = serializers.SerializerMethodField(read_only=True)

    topic_image = serializers.SerializerMethodField(read_only=True)

    topic_description = serializers.SerializerMethodField(read_only=True)
    plugin_references = PostPluginReferenceSerializer(many=True, required=False)



    class Meta:

        model = Post

        fields = [

            'id', 'topic', 'topic_name', 'topic_image', 'topic_description',
            'plugin_references',

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

    def to_internal_value(self, data):
        # Support multipart/form-data where plugin_references is sent as a JSON string
        if isinstance(data, dict) or hasattr(data, 'dict'):
            raw_refs = data.get('plugin_references')
            if isinstance(raw_refs, str):
                try:
                    mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
                    mutable_data['plugin_references'] = json.loads(raw_refs)
                    data = mutable_data
                except Exception:
                    pass
        return super().to_internal_value(data)

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
        # Uses in-memory prefetched reactions
        for r in obj.reactions.all():
            summary[r.emoji] = summary.get(r.emoji, 0) + 1
        return summary

    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user and request.user.is_authenticated:
            target_user_id = request.user.id
            # Iterate through in-memory prefetched reactions to eliminate per-post queries
            for r in obj.reactions.all():
                if r.user_id == target_user_id:
                    return r.emoji
        return None

    def get_comments_count(self, obj):
        # Uses SQL-annotated count from get_queryset if present
        if hasattr(obj, 'annotated_comments_count'):
            return obj.annotated_comments_count
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





class EditorialUserSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()

    avatar = serializers.SerializerMethodField()

    role = serializers.SerializerMethodField()



    class Meta:

        model = User

        fields = ['id', 'name', 'avatar', 'role']



    def get_name(self, obj):

        full_name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()

        return full_name if full_name else obj.phone



    def get_avatar(self, obj):

        if obj.profile_image:

            return obj.profile_image.url

        return None



    def get_role(self, obj):

        topic = self.context.get('topic')

        if topic and topic.created_by_id == obj.id:

            return 'creator'

        if topic and topic.admins.filter(user_id=obj.id).exists():

            return 'admin'

        return 'editor'





class PostEditProposalSerializer(serializers.ModelSerializer):

    editor = EditorialUserSerializer(read_only=True)

    reviewed_by = EditorialUserSerializer(read_only=True)

    post_id = serializers.PrimaryKeyRelatedField(

        queryset=Post.objects.all(),

        source='post',

        write_only=True,

        required=False

    )

    postId = serializers.IntegerField(source='post.id', read_only=True)

    originalContent = serializers.CharField(source='original_content', read_only=True)

    proposedContent = serializers.CharField(source='proposed_content', read_only=True)

    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    reviewedAt = serializers.DateTimeField(source='reviewed_at', read_only=True)

    reviewNote = serializers.CharField(source='review_note', required=False, allow_blank=True)

    postTitle = serializers.SerializerMethodField()



    class Meta:

        model = PostEditProposal

        fields = [

            'id', 'post_id', 'postId', 'postTitle', 'editor',

            'original_content', 'originalContent',

            'proposed_content', 'proposedContent',

            'reason', 'status', 'reviewed_by', 'reviewedAt', 'reviewNote',

            'created_at', 'createdAt', 'updated_at'

        ]

        read_only_fields = [

            'id', 'editor', 'original_content', 'originalContent', 'proposedContent', 'status',

            'reviewed_by', 'reviewed_at', 'created_at', 'updated_at'

        ]



    def validate(self, attrs):

        if self.instance is None and 'post' not in attrs:

            raise serializers.ValidationError({"post_id": "شناسه پست الزامی است."})

        return super().validate(attrs)



    def to_internal_value(self, data):

        data = data.copy() if hasattr(data, 'copy') else dict(data)

        if 'proposedContent' in data and 'proposed_content' not in data:

            data['proposed_content'] = data['proposedContent']

        if 'postId' in data and 'post_id' not in data:

            data['post_id'] = data['postId']

        return super().to_internal_value(data)



    def get_postTitle(self, obj):

        if obj.post and obj.post.topic:

            return obj.post.topic.name

        return ""





class PostEditHistorySerializer(serializers.ModelSerializer):

    editor = EditorialUserSerializer(read_only=True)

    approved_by = EditorialUserSerializer(read_only=True)

    approvedBy = EditorialUserSerializer(source='approved_by', read_only=True)

    postId = serializers.IntegerField(source='post.id', read_only=True)

    proposalId = serializers.UUIDField(source='proposal.id', read_only=True)

    previousContent = serializers.CharField(source='previous_content', read_only=True)

    newContent = serializers.CharField(source='new_content', read_only=True)

    summaryOfChanges = serializers.CharField(source='summary_of_changes', read_only=True)

    appliedAt = serializers.DateTimeField(source='applied_at', read_only=True)



    class Meta:

        model = PostEditHistory

        fields = [

            'id', 'postId', 'proposalId', 'editor', 'approved_by', 'approvedBy',

            'previous_content', 'previousContent',

            'new_content', 'newContent',

            'summary_of_changes', 'summaryOfChanges',

            'applied_at', 'appliedAt'

        ]

        read_only_fields = fields

class AyahSummaryQuerySerializer(serializers.Serializer):
    surah = serializers.IntegerField(min_value=1, max_value=114, required=True)
