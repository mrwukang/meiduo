from django_redis import get_redis_connection
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_jwt.views import ObtainJSONWebToken

from carts.utils import merge_cart_cookie_to_redis
from goods.models import SKU
from goods.serializers import SKUSerializer
from users.models import User
from users.serializers import RegisterCreateSerializer, UserDetailSerializer, EmailSerializer, AddressSerializer, \
    AddressTitleSerializer, UserBrowsingHistorySerializer
from users.utils import check_verify_email_token


class RegisterUsernameAPIView(APIView):
    """
    获取用户名的个数
    GET:  /users/usernames/(?P<username>\w{5,20})/count/
    """
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        context = {
            'username': username,
            'count': count,
        }
        return Response(context)


class RegisterPhoneCountAPIView(APIView):
    """
    获取手机号的个数
    GET:  users/phones/(?P<mobile>1[3456789]\d{9})/count/
    """

    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        context = {
            'count': count,
            'mobile': mobile,
        }
        return Response(context)


class RegisterCreateView(GenericAPIView):
    """
    用户注册
    POST:   /users/
    """
    serializer_class = RegisterCreateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        return Response(data=data)


class UserAuthorizationView(ObtainJSONWebToken):
    """
    用户登陆时使用的视图
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 如果验证通过，说明用户登陆成功
            user = serializer.validated_data.get("user")

            # 合并购物车
            response = merge_cart_cookie_to_redis(request, user, response)
        return response


class UserDetailView(RetrieveAPIView):
    """
        获取登录用户的信息
        GET /users/infos/
        既然是登录用户,我们就要用到权限管理
        在类视图对象中也保存了请求对象request
        request对象的user属性是通过认证检验之后的请求用户对象
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    """
    保存邮箱
    PUT /users/emails/
    """

    permission_classes = [IsAuthenticated]

    serializer_class = EmailSerializer

    def get_object(self):
        return self.request.user


class VerificationEmail(APIView):
    """
    验证邮箱
    GET:  /users/emails/verification/
    """
    def get(self, request):
        token = request.query_params.get("token")
        if not token:
            return Response({"message": "缺少token"}, status=status.HTTP_400_BAD_REQUEST)

        user = check_verify_email_token(token=token)
        if not user:
            return Response({"message": "无效的token"}, status=status.HTTP_400_BAD_REQUEST)

        user.email_active = True
        user.save()
        return Response({"message": "邮箱验证成功"}, status=status.HTTP_200_OK)


class AddressViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin,
    mixins.DestroyModelMixin, GenericViewSet):
    """
    收货地址视图集
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        count = request.user.addresses.count()
        if count >= 20:
            return Response({'message': '保存地址数量已经达到上限'}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """展示所有的收货地址"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'addresses': serializer.data,
            'limit': '20',
        })

    @action(methods=['put'], detail=True)
    def status(self, request, pk):
        """修改默认地址"""
        user = request.user
        address = self.get_object()
        user.default_address = address
        user.save()
        return Response({"default_address": user.default_address_id}, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def title(self, request, pk):
        """修改地址标题"""
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserBrowsingHistoryView(GenericAPIView):
    """
    用户浏览历史记录
    POST /users/browerhistories/
    GET  /users/browerhistories/
    数据只需要保存到redis中
    """
    serializer_class = UserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def post(self, request):
        """增加数据到redis中"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def get(self, request):
        """查询用户的浏览历史"""

        user_id = request.user.id
        # 连接redis
        redis_conn = get_redis_connection("history")
        # 获取用户浏览历史
        history_sku_ids = redis_conn.lrange('history_%s' % user_id, 0, 4)

        skus = []
        for sku_id in history_sku_ids:
            try:
                sku = SKU.objects.get(id=sku_id.decode())
            except SKU.DoesNotExist:
                return Response({"message": "内部查询错误"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                skus.append(sku)

        # TODO 为什么不直接得到skus呢, 因为如果这样写是无序的
        # skus = SKU.objects.filter(id__in=history_sku_ids)

        serializer = SKUSerializer(instance=skus, many=True)
        return Response(serializer.data)




