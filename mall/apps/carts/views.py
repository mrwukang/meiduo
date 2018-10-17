import base64
import pickle

from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework.views import APIView

from carts.serializers import CartSerializer


class CartView(APIView):
    """
    POST:  /cart/
    添加商品到购物车
    分为两种情况，一种是已经登陆， 一种是没有登陆
    """

    def perform_authentication(self, request):
        """进入此视图不立即检查JWT"""
        pass

    def post(self, request):
        """
        获取数据，进行校验
        如果是登陆用户，则将数据保存在redis
        如果用户未登录，则将数据保存在cookie中
        """
        data = request.data
        serializer = CartSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        # 获取商品ID，count和是否选中
        sku_id = serializer.data.get("sku_id")
        count = serializer.data.get("count")
        selected = serializer.data.get("selected")

        # 判断用户是否登陆
        try:
            user = request.user
        except Exception:
            # 如果出错则说明用户未登录
            user = None
        if user and user.is_authenticated:
            # 将数据保存在redis中
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 记录购物车商品数量hash
            pl.hincrby('cart_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            # 返回数据
            return Response(serializer.data)

        else:
            # 如果用户没有登陆则将数据保存在cookie中
            cart_str = request.COOKIES.get('cart')

            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str))
            else:
                cart_dict = {}
            # 如果提交的有相同的商品，则更新
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]['count']
                count += origin_count
            # 将数据保存在字典中
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 设置cookie
            response = Response(serializer.data)
            cookie_cart = base64.b64encode(pickle.dumps(cart_dict))
            response.set_cookie(cookie_cart)
            return response



