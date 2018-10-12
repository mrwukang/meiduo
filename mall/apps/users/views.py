from django.shortcuts import render
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
# Create your views here.
from users.models import User
from users.serializers import RegisterCreateSerializer, UserDetailSerializer, EmailSerializer


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


class RegisterCreateView(CreateAPIView):
    """
    用户注册
    POST:   /users/
    """
    serializer_class = RegisterCreateSerializer
    # def post(self, request):
    #     serializer = RegisterCreateSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(data=serializer.data)


class UserDetailView(RetrieveAPIView):
    """
        获取登录用户的信息
        GET /users/
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
