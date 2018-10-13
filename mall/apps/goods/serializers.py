from rest_framework import serializers

from goods.models import SKU


class SKUSerializer(serializers.ModelSerializer):
    """获取热销商品时使用的序列化器"""

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'comments', 'default_image_url']

