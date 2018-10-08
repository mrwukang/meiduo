import re
from django.contrib.auth.backends import ModelBackend
from users.models import User


def jwt_response_payload_handler(token, user=None, request=None):
    """
       自定义jwt认证成功返回数据
       """

    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }


def get_user_by_account(account):
    try:
        if re.match(r'1[3456789]\d{9}', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        user = None

    return user


class UsernameMobileAuthBackend(ModelBackend):
    """
    自定义用户名或手机号认证
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)
        if user and user.check_password(password):
            return user

