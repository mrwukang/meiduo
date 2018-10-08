from QQLoginTool.QQtool import OAuthQQ
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from mall import settings
from oauth.serializers import QQAuthUserSerializer


class QQAuthURLView(APIView):
    """
    生成url 实现出现QQ授权登录视图
    GET:  /oauth/qq/authorization/?next=xxx
    """

    def get(self, request):
        # next表示从哪个页面进入到的登录页面，将来登录成功后，就自动回到那个页面
        next_url = request.query_params.get('next')
        if not next_url:
            next_url = '/'

        # 获取QQ登录页面网址
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next_url)
        login_url = oauth.get_qq_url()

        return Response({'login_url': login_url})


class QQAuthUserView(GenericAPIView):
    """
    用户扫码登录的回调处理
    /oauth/qq/user/?code=xxx
    """

    serializer_class = QQAuthUserSerializer

    def get(self, request):
        # 提取code参数
        code = request.query_params.get('code')
        if not code:
            return Response(data={'message': '缺少code'}, status=status.HTTP_400_BAD_REQUEST)
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 使用code向QQ服务器请求access_token
            access_token = oauth.get_access_token(code)

            # 使用access_token向QQ服务器请求openid
            openid = oauth.get_open_id(access_token)
        except Exception:
            return Response({'message': 'QQ服务异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
