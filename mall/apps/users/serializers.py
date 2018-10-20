from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from celery_tasks.email.tasks import send_verify_mail
from goods.models import SKU
from users.models import User, Address
from rest_framework import serializers
import re

from users.utils import generate_verify_email_url


class RegisterCreateSerializer(serializers.ModelSerializer):
    """
    创建用户使用的序列化器
    """
    password2 = serializers.CharField(max_length=20, min_length=8, label="校验密码", allow_null=False, allow_blank=False, write_only=True)
    sms_code = serializers.CharField(max_length=6, min_length=6, label="短信验证码", allow_blank=False, allow_null=False, write_only=True)
    allow = serializers.CharField(label="是否同意条款", allow_null=False, allow_blank=False, write_only=True)
    token = serializers.CharField(label='登录状态token', required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', 'token']
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

        # 补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'mobile', 'email', 'email_active']


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']
        extra_kwargs = {
            'eamil': {'required': True},
        }

    def validate(self, attrs):
        email = attrs.get("email")
        if not re.match(r'^[a-zA-Z0-9_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z0-9]{2,6}$', email):
            raise serializers.ValidationError("邮箱格式不正确")
        return attrs

    def update(self, instance, validated_data):
        id = instance.id
        email = validated_data['email']
        instance.email = email
        instance.save()

        # 发送激活邮件
        # 生成激活链接
        verify_url = generate_verify_email_url(id, email)
        # 发送,注意调用delay方法
        send_verify_mail.delay(email, verify_url)
        return instance


class AddressSerializer(serializers.ModelSerializer):
    """
    新建收货地址时使用的序列化器
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def create(self, validated_data):
        # Address模型类中有user属性,将user对象添加到模型类的创建参数中
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    """修改地址标题的时候使用的序列化器"""
    class Meta:
        model = Address
        fields = ['title']


class UserBrowsingHistorySerializer(serializers.Serializer):
    """
    添加到用户浏览历史使用的序列化器
    """
    sku_id = serializers.IntegerField(label="商品编号", required=True, min_value=1)

    def validate(self, attrs):
        """判断sku_id是否正确"""
        sku_id = attrs.get("sku_id")
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            raise serializers.ValidationError("商品编号错误")
        return attrs

    def create(self, validated_data):
        """将sku_id保存到redis中"""
        # 获取用户的id
        user_id = self.context['request'].user.id
        # 获取商品的id
        sku_id = validated_data.get("sku_id")
        redis_conn = get_redis_connection('history')
        # 如果本商品的信息已经存在，则删除
        redis_conn.lrem('history_%s' % user_id, 0, sku_id)
        redis_conn.lpush('history_%s' % user_id, sku_id)
        # 最多只保存5条记录
        redis_conn.ltrim('history_%s' % user_id, 0, 4)
        return validated_data

