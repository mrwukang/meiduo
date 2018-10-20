import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from carts.utils import merge_cart_cookie_to_redis
from mall import settings
from QQLoginTool.QQtool import OAuthQQ

from oauth.models import OAuthQQUser
from oauth.serializers import QQAuthUserSerializer
from oauth.utils import generate_save_user_token

logger = logging.getLogger("meiduo")

class QQAuthURLView(APIView):
    """
    获得QQ扫码登录的页面
     GET:   oauth/qq/authorization/
    """
    def get(self, request):
        """
        返回QQ扫码登录的url
        """
        state = request.query_params.get("next")
        if not state:
            state = '/'
        client_id = settings.QQ_CLIENT_ID
        client_secret = settings.QQ_CLIENT_SECRET
        redirect_uri = settings.QQ_REDIRECT_URI
        oauthqq = OAuthQQ(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, state=state)
        qq_login_url = oauthqq.get_qq_url()
        return Response({'login_url': qq_login_url})


class QQAuthUserView(APIView):
    """
    URL: oauth/qq/user/
    如果是get请求，则是为了获得openid
    如果是post请求，则是为了提交数据
    """
    def get(self, request):

        # 创建OAuthQQ对象
        code = request.query_params.get('code')
        client_id = settings.QQ_CLIENT_ID
        client_secret = settings.QQ_CLIENT_SECRET
        redirect_uri = settings.QQ_REDIRECT_URI
        oauthqq = OAuthQQ(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
        # 获取扫码用户的openid
        try:
            token = oauthqq.get_access_token(code)
            openid = oauthqq.get_open_id(token)
        except Exception as e:
            logger.error(e)
            return Response({"message": "获取openid失败"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            qq_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果没有对应的用户，则将加密后的open_id返回
            access_token = generate_save_user_token(openid)
            return Response({"access_token": access_token})
        else:
            user = qq_user.user
            # 如果找到了openid对应的用户，则返回该用户的token丶user_id和username
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            response = Response({
                "token": token,
                "user_id": user.id,
                "username": user.username,
            })
            response = merge_cart_cookie_to_redis(request, user, response)

            return response

    def post(self, request):
        """
        如果是post方式提交，则说明是为了绑定用户
        判断用户手机号是否已经创建了用户，如果已经创建了，则直接绑定，如果没有，则创建用户后绑定
        """
        data = request.data
        serializer = QQAuthUserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 绑定用户
        user = serializer.save()
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        response = Response({
            "token": token,
            "user_id": user.id,
            "username": user.username,
        })
        response = merge_cart_cookie_to_redis(request, user, response)
        return response


