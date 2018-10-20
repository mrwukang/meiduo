import time

from decimal import Decimal

from django_redis import get_redis_connection
from rest_framework import serializers

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods


class CartSKUSerializer(serializers.ModelSerializer):
    """获取购物车数据时使用的序列化器"""
    count = serializers.IntegerField(label="数量", required=False)

    class Meta:
        model = SKU
        fields = ('id', 'count', 'name', 'default_image_url', 'price')


class OrderSettlementSerializer(serializers.Serializer):
    """
    获取订单数据时使用的序列化器
    """
    freight = serializers.DecimalField(label="运费", max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)


class OrderCommitSerializer(serializers.ModelSerializer):
    """
    创建订单时使用的序列化器
    """

    class Meta:
        model = OrderInfo
        fields = ('pay_method', 'address', 'order_id')
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'pay_method': {
                'required': True,
                'write_only': True
            },
            'address': {
                'required': True,
                'write_only': True
            }
        }

    def create(self, validated_data):
        """创建订单"""
        # 获取当前下单用户
        user = self.context['request'].user
        # 生成订单编号
        order_id = time.strftime('%Y%m%d%H%M%S', time.localtime()) + '%09d' % user.id
        # 保存订单基本信息数据 OrderInfo
        address = validated_data.get('address')
        pay_method = validated_data.get('pay_method')

        order = OrderInfo.objects.create(
            order_id=order_id,
            user=user,
            address=address,
            total_count=0,
            total_amount=Decimal('0'),
            freight=Decimal('10'),
            pay_method=pay_method,
            status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH'] else
            OrderInfo.ORDER_STATUS_ENUM['UNPAID']
        )
        # 从redis中获取购物车结算商品数据
        # 连接redis
        redis_conn = get_redis_connection("cart")
        redis_dict = redis_conn.hgetall("cart_%d" % user.id)
        redis_selected = redis_conn.smembers("cart_selected_%d" % user.id)

        # 遍历结算商品：
        cart_dict = {}
        for sku_id in redis_selected:
            # 获取商品的id和数量
            count = int(redis_dict[sku_id])
            sku_id = int(sku_id)

            # 判断商品库存是否充足
            try:
                sku = SKU.objects.get(pk=sku_id)
            except SKU.DoesNotExist:
                raise serializers.ValidationError("获取商品错误")
            if count > sku.stock:
                raise serializers.ValidationError("库存不足")
            # 将商品的id和数量保存到字典中
            cart_dict[int(sku_id)] = count

            # 减少商品库存，增加商品销量
            sku.stock -= count
            sku.sales += count
            sku.save()

            # 保存订单商品数据
            order.total_count += count
            order.total_amount += (sku.price * count)
            # 创建订单商品
            OrderGoods.objects.create(
                order=order,
                sku=sku,
                count=count,
                price=sku.price,
            )
        # 保存订单
        order.save()

        # 清除购物车中已经结算的商品
        pl = redis_conn.pipeline()
        cart_select = cart_dict.keys()
        pl.hdel("cart_%d" % user.id, *cart_select)
        pl.srem("cart_selected_%d" % user.id, *cart_select)
        pl.execute()
        return order


