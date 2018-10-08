from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
# Create your views here.
from users.models import User
from users.serializers import RegisterCreateSerializer


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


