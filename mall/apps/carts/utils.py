import base64
import pickle

from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """
    合并用户的购物车数据，将用户cookie中的购物车信息保存到cookie中
    :param request: 用户的请求对象
    :param user: 当前登陆的用户
    :param response: 响应对象
    :return: response
    """
    # 得到本地cookie
    cookie_str = request.COOKIES.get("cart")
    # 如果有存储的购物车数据，则将购物车数据添加到user对应的redis中
    if cookie_str:
        # 获得cookie和redis中的购物车数据
        cart_dict_cookie = pickle.loads(base64.b64decode(cookie_str))
        redis_conn = get_redis_connection("cart")
        cart_dict_redis = redis_conn.hgetall("cart_%s" % user.id)
        # 将redis中的数据转化为字典
        cart_dict = {}
        cart_selected = []
        for sku_id, count in cart_dict_redis.items():
            cart_dict[int(sku_id)] = int(count)

        for sku_id, count_selected_dict in cart_dict_cookie.items():
            # 如果商品在用户的购物车中已经存在，则将两个数量相加，如果不存在，则添加新纪录
            if cart_dict.get(sku_id):
                cart_dict[sku_id] = int(cart_dict.get(sku_id)) + count_selected_dict['count']
            else:
                cart_dict[sku_id] = count_selected_dict['count']
            if count_selected_dict['selected']:
                cart_selected.append(sku_id)

        # 将数据保存到redis中
        pl = redis_conn.pipeline()
        pl.hmset('cart_%s' % user.id, cart_dict)
        if cart_selected:
            pl.sadd('cart_selected_%s' % user.id, *cart_selected)
        pl.execute()
        # 返回原有的响应数据
        return response

    # 如果本地没有存储的购物车数据
    else:
        return response


