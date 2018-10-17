from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings
from users.models import User


def generate_verify_email_url(id, email):
    """生成验证邮件地址"""
    serializer = Serializer(settings.SECRET_KEY, 3600)

    # 加载用户信息
    token = serializer.dumps({'user_id': id, 'email': email})
    # 注意拼接的过程中对 token进行decode操作
    verify_url = settings.EMAIL_PREFIX + '/success_verify_email.html?token=' + token.decode()

    return verify_url


def check_verify_email_token(token):
    """验证邮件携带的token是否正确"""
    serializer = Serializer(settings.SECRET_KEY, 3600)

    # 通过token加载用户信息
    try:
        result = serializer.loads(token)
    except BadData:
        return None

    id = result.get("user_id")
    email = result.get("email")
    try:
        user = User.objects.get(id=id, email=email)
    except User.DoesNotExist:
        return None
    return user
