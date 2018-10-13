from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings


def generate_save_user_token(openid):
    """将openid加密"""
    s = Serializer(settings.SECRET_KEY, 3600)
    data = {'openid': openid}
    access_token = s.dumps(data)
    return access_token


def check_save_user_token(access_token):
    s = Serializer(settings.SECRET_KEY, 3600)
    try:
        data = s.loads(access_token)
    except BadData:
        return None

    return data.get("openid")


