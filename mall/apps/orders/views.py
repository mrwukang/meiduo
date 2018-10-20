from decimal import Decimal
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import SKU
from orders.serializers import OrderSettlementSerializer, OrderCommitSerializer


class OrderSettlementView(APIView):
    """
    订单结算，获取商品的详细信息
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获得数据"""
        user = request.user

        # 连接redis
        redis_conn = get_redis_connection("cart")
        redis_dict = redis_conn.hgetall("cart_%d" % user.id)
        redis_selected = redis_conn.smembers("cart_selected_%d" % user.id)

        # 将sku_id和count存储到字典中
        cart_dict = {}
        for sku_id in redis_selected:
            cart_dict[int(sku_id)] = int(redis_dict[sku_id])

        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart_dict.keys())
        for sku in skus:
            sku.count = cart_dict[int(sku.id)]
        # 运费
        freight = Decimal('10.00')
        serializer = OrderSettlementSerializer(instance={'freight': freight, 'skus': skus})
        return Response(serializer.data)


class OrderView(GenericAPIView):
    """
    保存订单
    POST /orders/

    登录用户
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderCommitSerializer

    def post(self, request):
        """提交订单"""
        data = request.data
        serializer =self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

