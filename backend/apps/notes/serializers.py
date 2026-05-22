from rest_framework import serializers
from .models import Note, Channel


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'name', 'bio', 'image', 'telegram_chat_id', 'bale_chat_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class NoteSerializer(serializers.ModelSerializer):
    channel = serializers.PrimaryKeyRelatedField(queryset=Channel.objects.all(), allow_null=True, required=False)
    is_sent_to_telegram = serializers.SerializerMethodField(read_only=True)
    is_sent_to_bale = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Note
        fields = [
            'id',
            'title',
            'content',
            'channel',
            'created_at',
            'updated_at',
            'send_to_telegram',
            'send_to_bale',
            'is_sent_to_telegram',
            'is_sent_to_bale',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_sent_to_telegram(self, obj):
        return bool(obj.telegram_message_id)

    def get_is_sent_to_bale(self, obj):
        return bool(obj.bale_message_id)