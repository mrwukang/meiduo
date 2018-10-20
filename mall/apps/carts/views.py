import base64
import pickle

from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from carts.serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer
from goods.models import SKU


class CartView(APIView):
    """
    POST        /cart/ 添加商品到购物车
    GET         /cart/ 获取购物车数据
    PUT         /cart/ 修改购物车数据
    DELETE      /cart/删除购物车数据
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
        # 对接受到的数据进行校验
        data = request.data
        serializer = CartSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        # 拿到校验后的数据
        sku_id = serializer.data.get('sku_id')
        count = serializer.data.get('count')
        selected = serializer.data.get('selected')

        # 判断用户是否登陆
        try:
            user = request.user
        except:
            user = None

        if user and user.is_authenticated:
            # 如果用户登陆，则将数据保存到redis中
            redis_conn = get_redis_connection("cart")
            pl = redis_conn.pipeline()
            pl.hincrby('cart_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(data=serializer.data)

        else:
            # 如果用户未登录，则将数据保存到cookie中
            cart_str = request.COOKIES.get("cart")
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str))
            else:
                cart_dict = {}
            # 如果原来的购物车中已经存在了此商品，则在原来数量的基础上增加本次数量
            if sku_id in cart_dict:
                original_count = cart_dict[sku_id].get('count')
                count += original_count
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 返回响应，响应中设置cookie
            response = Response(data=request.data)
            cookie_cart = base64.b64encode(pickle.dumps(cart_dict))
            response.set_cookie('cart', cookie_cart)
            return response

    def get(self, request):
        """
        获取购物车的数据
        判断用户是否登陆
            如果用户登陆从redis中查询数据，
            如果用户未登录从cookie中查询数据
        获取所有商品的数据
        """
        # 判断用户是否登陆
        try:
            user = request.user
        except Exception:
            user = None

        if user and user.is_authenticated:
            # 如果用户登陆，则从redis中得到数据
            redis_conn = get_redis_connection("cart")
            # 得到redis中的hash数据和set数据
            redis_cart = redis_conn.hgetall("cart_%s" % user.id)
            redis_cart_selected = redis_conn.smembers("cart_selected_%s" % user.id)
            # 将数据转化成和cookie一样的字典格式
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_cart_selected
                }
        else:
            # 如果用户没有登陆，则从cookie中查找数据
            cart_str = request.COOKIES.get("cart")
            if not cart_str:
                return Response(data=None, status=status.HTTP_200_OK)
            else:
                cart_dict = pickle.loads(base64.b64decode(cart_str))

        # 遍历字典，得到数据
        skus = []
        for sku_id in cart_dict:
            try:
                sku = SKU.objects.get(pk=sku_id)
            except SKU.DoesNotExist:
                return Response({"message": "内部查询错误"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                skus.append(sku)
        # 给每一个sku对象赋予count和selected属性
        for sku in skus:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        # 返回数据
        serializer = CartSKUSerializer(instance=skus, many=True)
        return Response(data=serializer.data)

    def put(self, request):
        """修改购物车数据"""

        # 对接受到的数据进行校验
        data = request.data
        serializer = CartSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        # 拿到校验后的数据
        sku_id = serializer.data.get('sku_id')
        count = serializer.data.get('count')
        selected = serializer.data.get('selected')

        # 判断用户是否登陆
        try:
            user = request.user
        except:
            user = None

        if user and user.is_authenticated:
            # 如果用户登陆，则将数据保存到redis中
            redis_conn = get_redis_connection("cart")
            pl = redis_conn.pipeline()
            pl.hset('cart_%s' % user.id, sku_id, count)

            # 如果此商品选中了，则在set中增加sku_id，否则从set中删除sku_id
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(data=serializer.data)

        else:
            # 如果用户未登录，则将数据保存到cookie中
            cart_str = request.COOKIES.get("cart")
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str))
            else:
                cart_dict = {}
            # 如果原有购物车数据之间中有本商品数据，则覆盖
            # 如果原有购物车中没有此商品数据，则新增
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 返回响应，响应中设置cookie
            response = Response(data=request.data)
            cookie_cart = base64.b64encode(pickle.dumps(cart_dict))
            response.set_cookie('cart', cookie_cart)
            return response

    def delete(self, request):
        """通过传入的sku_id删除redis或者cookie中的数据"""
        # 接收数据，只需要接收一个sku_id就行了
        data = request.data
        serializer = CartDeleteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.data.get("sku_id")

        # 判断用户是否登陆
        try:
            user = request.user
        except Exception:
            user = None

        # 如果用户登陆
        if user and user.is_authenticated:
            redis_conn = get_redis_connection("cart")
            pl = redis_conn.pipeline()
            pl.hdel("cart_%s" % user.id, sku_id)
            pl.srem("cart_selected_%s" % user.id, sku_id)
            pl.execute()
            return Response(status=status.HTTP_204_NO_CONTENT)

        else:
            # 如果用户没有登陆，则从cookie中删除数据
            cart_str = request.COOKIES.get("cart")
            cart_dict = pickle.loads(base64.b64decode(cart_str))
            del cart_dict[sku_id]
            # 返回响应，响应中设置cookie
            response = Response(data=request.data)
            cookie_cart = base64.b64encode(pickle.dumps(cart_dict))
            response.set_cookie('cart', cookie_cart)
            return response


