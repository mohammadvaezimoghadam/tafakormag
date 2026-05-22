from rest_framework import serializers
from .models import User, BotConnectionToken


IRAN_MOBILE_REGEX = r'^09\d{9}$'
IRAN_MOBILE_ERROR = 'شماره موبایل باید به صورت 09123456789 باشد'

class UserSerializer(serializers.ModelSerializer):
    is_telegram_connected = serializers.SerializerMethodField()
    is_bale_connected = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['phone', 'is_telegram_connected', 'is_bale_connected']
        read_only_fields = ['phone', 'is_telegram_connected', 'is_bale_connected']

    def get_is_telegram_connected(self, obj):
        return bool(obj.telegram_chat_id)

    def get_is_bale_connected(self, obj):
        return bool(obj.bale_chat_id)


class RequestOTPSerializer(serializers.Serializer):
    phone = serializers.RegexField(
        regex=IRAN_MOBILE_REGEX,
        max_length=11,
        min_length=11,
        error_messages={
            'invalid': IRAN_MOBILE_ERROR
        }
    )
    force_sms = serializers.BooleanField(required=False, default=False)


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.RegexField(
        regex=IRAN_MOBILE_REGEX,
        max_length=11,
        min_length=11,
        error_messages={
            'invalid': IRAN_MOBILE_ERROR
        }
    )   
    otp = serializers.RegexField(
        regex=r'^\d{4}$',
        max_length=4,
        min_length=4,
        error_messages={
            'invalid': 'کد تأیید باید 4 رقم باشد'
        }
    )


class ConnectTokenResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotConnectionToken
        fields = ['token', 'platform', 'created_at']