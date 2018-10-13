from django_redis import get_redis_connection
from rest_framework import serializers

from oauth.models import OAuthQQUser
from oauth.utils import check_save_user_token
from users.models import User


class QQAuthUserSerializer(serializers.Serializer):
    """
    QQ号与帐号绑定时使用的序列化器
    """
    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    def validate(self, attrs):
        access_token = attrs.get("access_token")
        mobile = attrs.get("mobile")
        sms_code = attrs.get("sms_code")
        password = attrs.get("password")

        if not all([access_token, mobile, password, sms_code]):
            raise serializers.ValidationError("参数不全")
        # 获取身份凭证
        openid = check_save_user_token(access_token)
        if not openid:
            raise serializers.ValidationError('无效的access_token')
        attrs['openid'] = openid
        # 验证短信验证码是否正确
        redis_conn = get_redis_connection('code')
        sms_code_redis = redis_conn.get('sms_%s' % mobile)
        if not sms_code_redis:
            raise serializers.ValidationError("短信验证码已经过期")

        # 通过手机号查找用户，如果用户存在，则验证用户密码是否正确
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            user = None
        else:
            if not user.check_password(password):
                raise serializers.ValidationError("用户密码错误")
        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        user = validated_data.get("user")
        if not user:
            user = User.objects.create(
                mobile=validated_data.get("mobile"),
                username=validated_data.get("mobile"),
                password=validated_data.get('password')
            )
            user.set_password(validated_data.get('password'))
            user.save()
        OAuthQQUser.objects.create(user=user, openid=validated_data.get('openid'))
        return user
