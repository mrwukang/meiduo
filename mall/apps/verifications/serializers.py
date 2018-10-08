from django_redis import get_redis_connection
from redis.exceptions import RedisError
from rest_framework import serializers
import logging

logger = logging.getLogger("meiduo")


class RegisterSMSCodeSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=4, min_length=4, required=True, label="图形验证码")
    image_code_id = serializers.UUIDField(label="UUid")

    def validate(self, attrs):
        text = attrs.get('text')
        image_code_id = attrs.get('image_code_id')
        if not all([text, image_code_id]):
            raise serializers.ValidationError("参数不全")
        # 从redis中取出存储的图形验证码
        redis_conn = get_redis_connection('code')
        text_redis = redis_conn.get('img_%s' % image_code_id)
        if not text_redis:
            raise serializers.ValidationError("验证码已经过期")
        if text_redis.decode().lower() != text.lower():
            raise serializers.ValidationError("验证码输入错误")

        # 将redis中的验证码删除
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except RedisError as e:
            logger.error(e)
        return attrs
