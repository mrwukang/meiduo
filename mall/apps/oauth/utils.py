from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData

from mall import settings


def generate_save_user_token(openid):
    """
    生成保存用户数据的token
    :param openid: 用户的openid
    :return: token
    """
    serializer = Serializer(settings.SECRET_KEY, expires_in=3600)
    data = {'openid': openid}
    # 加密
    token = serializer.dumps(data)
    return token.decode()


def check_save_user_token(access_token):
    """
    检验保存用户数据的token
    :param access_token: token
    :return: openid or None
    """
    serializer = Serializer(settings.SECRET_KEY, expires_in=3600)
    try:
        # 解密
        data = serializer.loads(access_token)
    except BadData:
        return None
    else:
        return data.get('openid')
