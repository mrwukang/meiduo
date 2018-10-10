from QQLoginTool.QQtool import OAuthQQ
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from mall import settings
from oauth.models import OAuthQQUser
from oauth.serializers import QQAuthUserSerializer
from oauth.utils import generate_save_user_token


class QQAuthURLView(APIView):
    """
    生成url 实现出现QQ授权登录视图
    GET:  /oauth/qq/authorization/?next=xxx
    """
    def get(self, request):
        next_url = request.query_params.get('next')
        if not next_url:
            next_url = '/'
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET, redirect_uri=settings.QQ_REDIRECT_URI, state=next_url)
        login_url = oauth.get_qq_url()
        return Response({'login_url': login_url})


class QQAuthUserView(GenericAPIView):
    """
    扫码登录，先是get方式，得到扫码QQ号的code
    通过code得到access_token
    通过access_token得到open_id
    通过open_id在tb_oauth_qq中寻找对象，如果有，就返回对象的token，username，id


    如果没有寻找到对象，就返回access_token
    并显示关联界面
    填写mobile，password，图片验证码，短信验证码后ajax提交数据
    验证短信验证码，从tb_users中寻找mobile=mobile的对象，如果有，则验证密码，密码正确则关联

    如果没有对象，则创建对象并关联
    """
    serializer_class = QQAuthUserSerializer

    def get(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({"message":"没有code"}, status=status.HTTP_400_BAD_REQUEST)
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            access_token = oauth.get_access_token(code=code)
            open_id = oauth.get_open_id(access_token=access_token)
        except Exception:
            return Response({'message': 'QQ服务异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            oauth_user = OAuthQQUser.objects.get(openid=open_id)
        except OAuthQQUser.DoesNotExist:
            access_token_openid = generate_save_user_token(open_id)
            return Response({'access_token': access_token_openid})
        else:
            user = oauth_user.user
            # 如果openid已绑定美多商城用户，直接生成JWT token，并返回
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            # 获取oauth_user关联的user
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            response = Response({
                'token': token,
                'username': user.username,
                'user_id': user.id,
            })
            return response

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_excerption=True)
        user = serializer.save()

        # 这四步就是生成token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        response = Response({
            'token': token,
            'username': user.username,
            'user_id': user.id,
        })
        return response
