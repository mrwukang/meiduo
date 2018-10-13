from django.shortcuts import render
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
# Create your views here.
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from users.models import User
from users.serializers import RegisterCreateSerializer, UserDetailSerializer, EmailSerializer, AddressSerializer, \
    AddressTitleSerializer


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
    # serializer_class = RegisterCreateSerializer
    def post(self, request):
        serializer = RegisterCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        return Response(data=data)


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

        user = User.check_verify_email_token(token=token)
        if not user:
            return Response({"message": "无效的token"}, status=status.HTTP_400_BAD_REQUEST)

        user.email_active = True
        user.save()
        return Response({"message": "邮箱验证成功"}, status=status.HTTP_200_OK)


class AddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin,
                     GenericViewSet):
    # 添加用户权限
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
    def title(self, request, pk=None, address_id=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """
        修改默认地址
        """
        address = self.get_object()
        user = request.user
        user.default_address = address
        user.save()
        return Response({"default_address": user.default_address_id}, status=status.HTTP_200_OK)
