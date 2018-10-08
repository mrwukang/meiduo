from django_redis import get_redis_connection

from users.models import User
from rest_framework import serializers
import re

class RegisterCreateSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(max_length=20, min_length=8, label="校验密码", allow_null=False, allow_blank=False, write_only=True)
    sms_code = serializers.CharField(max_length=6, min_length=6, label="短信验证码", allow_blank=False, allow_null=False, write_only=True)
    allow = serializers.CharField(label="是否同意条款", allow_null=False, allow_blank=False, write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow']
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            },
        }

    def validate_mobile(self, value):
        if not re.match(r'1[3456789]\d{9}', value):
            raise serializers.ValidationError("手机号码不符合格式")
        return value

    def validate_allow(self, value):
        if value != 'true':
            raise serializers.ValidationError("未同意协议")
        return value

    def validate(self, attrs):
        sms_code = attrs.get('sms_code')
        mobile = attrs.get('mobile')
        redis_conn = get_redis_connection('code')
        sms_code_redis = redis_conn.get('sms_%s' % mobile)
        if not sms_code_redis:
            raise serializers.ValidationError("短信验证码已经过期")
        if sms_code_redis.decode() != sms_code:
            raise serializers.ValidationError("短信验证码输入错误")

        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError('两次密码输入不一致')
        return attrs

    def create(self, validated_data):
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        user = super().create(validated_data)

        user.set_password(validated_data['password'])
        user.save()
        return user


