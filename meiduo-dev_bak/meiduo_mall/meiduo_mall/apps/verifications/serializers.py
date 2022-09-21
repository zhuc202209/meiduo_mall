from rest_framework import serializers
from django_redis import get_redis_connection
from redis.exceptions import RedisError
import logging

logger = logging.getLogger('django')


class CheckImageCodeSerialzier(serializers.Serializer):
    """
    图片验证码校验序列化器
    GenericAPIView  ->  get_seriliazer()  context

    """
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(min_length=4, max_length=4)

    def validate(self, attrs):
        """校验图片验证码是否正确"""
        image_code_id = attrs['image_code_id']
        text = attrs['text']

        # 查询redis数据库，获取真实的验证码
        redis_conn = get_redis_connection('verify_codes')
        real_image_code = redis_conn.get('img_%s' % image_code_id)

        if real_image_code is None:
            # 过期或者不存在
            raise serializers.ValidationError('无效的图片验证码')

        # 删除redis中的图片验证码，防止用户对同一个进行多次请求验证
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except RedisError as e:
            logger.error(e)

        # 对比
        real_image_code = real_image_code.decode()
        if real_image_code.lower() != text.lower():
            raise serializers.ValidationError('图片验证码错误')

        # redis中发送短信验证码的标志 send_flag_<mobile>  : 1, 由redis维护60s的有效期
        mobile = self.context['view'].kwargs.get('mobile')
        if mobile:
            send_flag = redis_conn.get('send_flag_%s' % mobile)
            if send_flag:
                raise serializers.ValidationError('发送短信次数过于频繁')

        return attrs



