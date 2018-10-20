from rest_framework import serializers

from goods.models import SKU


class CartSerializer(serializers.Serializer):
    """
    添加购物车时使用的序列化器
    """
    sku_id = serializers.IntegerField(label="sku_id", min_value=1, required=True)
    count = serializers.IntegerField(label="数量", min_value=1, required=True)
    selected = serializers.BooleanField(label="是否选择", required=False, default=True)

    def validate(self, attrs):
        """校验商品ID和数量是否符合要求"""
        sku_id = attrs.get("sku_id")
        count = attrs.get("count")
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            raise serializers.ValidationError("没有此商品")
        if sku.stock < count:
            raise serializers.ValidationError("库存不足")
        return attrs


class CartSKUSerializer(serializers.ModelSerializer):
    """获取购物车数据时使用的序列化器"""
    count = serializers.IntegerField(label="数量", required=False)
    selected = serializers.IntegerField(label="是否勾选", required=False)

    class Meta:
        model = SKU
        fields = ('id', 'count', 'selected', 'name', 'default_image_url', 'price')


class CartDeleteSerializer(serializers.Serializer):
    """
    删除购物车数据时使用的序列化器
    """
    sku_id = serializers.IntegerField(label="sku_id", min_value=1, required=True)

    def validate_sku_id(self, value):
        """检查sku_id是否存在"""
        try:
            sku = SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError("没有此商品")
        return value

