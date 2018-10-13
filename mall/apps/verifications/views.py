import random

from django.http.response import HttpResponse
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django_redis import get_redis_connection

from celery_tasks.sms.tasks import send_sms_code
from libs.captcha.captcha import captcha
from verifications.serializers import RegisterSMSCodeSerializer


class RegisterImageCodeView(APIView):
    """
    生成验证码
    GET verifications/imagecodes/(?P<image_code_id>.+)/
    需要通过JS生成一个唯一码,以确保后台对图片进行校验
    """
    def get(self, request, image_code_id):
        text, image = captcha.generate_captcha()
        print(text)
        redis_conn = get_redis_connection('code')
        redis_conn.setex('img_%s' % image_code_id, 60, text)
        return HttpResponse(content=image, content_type="image/jpeg")


class RegisterSMSCodeView(APIView):
    """
    获取短信验证码
    GET /verifications/smscodes/(?P<mobile>1[3456789]\d{9})/?text=xxxx&image_code_id=xxxx
    获取短信验证码,首先需要校验 验证码
    """
    def get(self, request, mobile):
        query_params = request.query_params
        serializer = RegisterSMSCodeSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        redis_conn = get_redis_connection('code')
        if redis_conn.get('sms_flag_%s' % mobile):
            return Response(status=status.HTTP_429_TOO_MANY_REQUESTS)

        # 生成短信验证码
        sms_code = '%06d' % (random.randint(0, 999999))
        # send_sms_code.delay(mobile, sms_code)
        print(sms_code)
        redis_conn.setex('sms_%s' % mobile, 300, sms_code)
        redis_conn.setex('sms_flag_%s' % mobile, 60, 1)
        return Response({'message': 'OK', 'sms_code': sms_code})



