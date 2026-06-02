from rest_framework import serializers
from .models import User, BotConnectionToken


IRAN_MOBILE_REGEX = r'^09\d{9}$'
IRAN_MOBILE_ERROR = 'شماره موبایل باید به صورت 09123456789 باشد'

class UserSerializer(serializers.ModelSerializer):
    is_telegram_bot_connected = serializers.SerializerMethodField()
    is_bale_bot_connected = serializers.SerializerMethodField()
    is_telegram_otp_connected = serializers.SerializerMethodField()
    is_bale_otp_connected = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'phone', 
            'first_name',
            'last_name',
            'profile_image',
            'is_telegram_bot_connected', 'telegram_bot_username',
            'is_bale_bot_connected', 'bale_bot_username',
            'is_telegram_otp_connected', 'is_bale_otp_connected'
        ]
        read_only_fields = [
            'id',
            'phone', 
            'is_telegram_bot_connected', 'telegram_bot_username',
            'is_bale_bot_connected', 'bale_bot_username',
            'is_telegram_otp_connected', 'is_bale_otp_connected'
        ]

    def get_is_telegram_bot_connected(self, obj):
        return bool(obj.telegram_bot_token)

    def get_is_bale_bot_connected(self, obj):
        return bool(obj.bale_bot_token)

    def get_is_telegram_otp_connected(self, obj):
        return bool(obj.telegram_chat_id)

    def get_is_bale_otp_connected(self, obj):
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