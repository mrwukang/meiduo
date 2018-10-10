from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from mall import settings


class User(AbstractUser):
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')

    class Meta:
        db_table = "tb_users"
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def generate_verify_email_url(self):
        serializer = Serializer(settings.SECRET_KEY, 3600)

        # 加载用户信息
        token = serializer.dumps({'user_id': self.id, 'email': self.email})
        # 注意拼接的过程中对 token进行decode操作
        verify_url = 'http://www.meiduo.site:8080/success_verify_email.html?token=' + token.decode()

        return verify_url
