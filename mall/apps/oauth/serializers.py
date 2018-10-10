from django_redis import get_redis_connection
from rest_framework import serializers

from oauth.models import OAuthQQUser
from oauth.utils import check_save_user_token
from users.models import User


class QQAuthUserSerializer(serializers.Serializer):
    """
    创建与QQ关联的对象使用的序列化器
    """
    mobile = serializers.RegexField(label="手机号", regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(max_length=20, min_length=8, label="密码")
    sms_code = serializers.CharField(max_length=6, min_length=6, label="短信验证码")
    access_token = serializers.CharField(label="操作凭证")

    def validate(self, attrs):
        """校验传入的参数"""
        access_token = attrs.get('access_token')
        mobile = attrs.get('mobile')
        password = attrs.get('password')
        sms_code = attrs.get('sms_code')
        if not all([access_token, mobile, password, sms_code]):
            raise serializers.ValidationError("参数不全")

        open_id = check_save_user_token(access_token)
        if not open_id:
            raise serializers.ValidationError("无效的凭证")
        attrs['open_id'] = open_id

        # 判断sms_code是否正确
        redis_conn = get_redis_connection("code")
        sms_code_redis = redis_conn.get('sms_%s' % mobile)
        if not sms_code_redis:
            raise serializers.ValidationError("短信验证码已经过期")
        if sms_code_redis.decode() != sms_code:
            raise serializers.ValidationError("短信验证码错误")

        # 校验密码是否正确
        try:
            user = User.objects.get(mobile=mobile)
        except Exception:
            pass
        else:
            if not user.check_password(password):
                raise serializers.ValidationError("密码错误")

            attrs['user'] = user
        return attrs

    def create(self, validated_data):
        """创建与QQ关联的对象"""

        # 如果user已经存在
        user = validated_data.get('user')
        if not user:
            # 用户不存在,新建用户
            user = User.objects.create_user(
                username=validated_data['mobile'],
                password=validated_data['password'],
                mobile=validated_data['mobile'],
            )

        # 将用户绑定openid
        OAuthQQUser.objects.create(
            openid=validated_data['openid'],
            user=user
        )
        # 返回用户数据
        return user
