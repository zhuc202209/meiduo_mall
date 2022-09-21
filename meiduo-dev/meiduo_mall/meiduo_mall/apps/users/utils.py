from django.contrib.auth.backends import ModelBackend
import re

from .models import User

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
    """
    根据账号信息，查找用户对象
    :param account: 可以是手机号、用户名
    :return: User对象，None
    """
    try:
        # 判断account是否是手机号
        if re.match(r'^1[3-9]\d{9}$', account):
            # 根据手机号查询
            user = User.objects.get(mobile=account)
        else:
            # 根据username查询
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """
    自定义的认证方法后端
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 根据username查询用户对象， username 用户名 手机
        user = get_user_by_account(username)
        # 如果用户对象存在，调用check_password方法检查密码
        if user is not None and user.check_password(password):
            # 验证成功，返回对象
            return user









