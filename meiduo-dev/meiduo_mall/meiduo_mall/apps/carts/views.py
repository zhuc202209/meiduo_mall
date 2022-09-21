import base64
import pickle

from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer
from goods.models import SKU

# Create your views here.


class CartView(APIView):
    """
    购物车
    """
    def perform_authentication(self, request):
        """重写检查JWT token是否正确"""
        pass

    def post(self, request):
        """保存购物车数据"""
        # 检查前端发送的数据是否正确
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            # 前端携带了错误的 JWT  用户未登录
            user = None

        # 保存购物车数据
        if user is not None and user.is_authenticated:
            # 用户已登录 保存到redis中
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()

            # 购物车数据  hash
            pl.hincrby('cart_%s' % user.id, sku_id, count)

            # 勾选
            if selected:
                pl.sadd('cart_selected_%s' % user.id,  sku_id)

            pl.execute()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # 用户未登录，保存到cookie中
            # 尝试从cookie中读取购物车数据
            cart_str = request.COOKIES.get('cart')

            if cart_str:

                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

            # {
            #     sku_id: {
            #                 "count": xxx, // 数量
            #     "selected": True // 是否勾选
            # },
            # sku_id: {
            #     "count": xxx,
            #     "selected": False
            # },
            # ...
            # }

            # 如果有相同商品，求和
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            cookie_cart = base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 返回

            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            response.set_cookie('cart', cookie_cart)

            return response

    def get(self, request):
        """查询购物车数据"""
        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            # 前端携带了错误的 JWT  用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 如果用户登录，从redis查询
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall("cart_%s" % user.id)
            # {
            #     sku_id: count,
            #     sku_id: count
            # }
            cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

            # 将redis中的数据进行整合，形成一个字典，与cookie中解读的一致，方便数据库查询
            # {
            #     sku_id: {
            #                 "count": xxx, // 数量
            #     "selected": True // 是否勾选
            # },
            # sku_id: {
            #     "count": xxx,
            #     "selected": False
            # },
            # ...
            # }
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }
        else:
            # 如果用户未登录，从cookie中查询
            cart_str = request.COOKIES.get('cart')

            if cart_str:

                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

        sku_id_list = cart_dict.keys()

        # 数据库查询sku对象
        sku_obj_list = SKU.objects.filter(id__in=sku_id_list)
        # 向结果集中补充count 和 selected
        for sku in sku_obj_list:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        # 序列化返回
        serializer = CartSKUSerializer(sku_obj_list, many=True)
        return Response(serializer.data)

    def put(self, request):
        # 检查前端发送的数据是否正确
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            # 前端携带了错误的 JWT  用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 如果用户登录，修改redis数据
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hset('cart_%s' % user.id, sku_id, count)
            if selected:
                # 勾选增加记录
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                # 未勾选 删除记录
                pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()

            return Response(serializer.data)

        else:
            # 如果用户未登录，修改cookie数据
            cart_str = request.COOKIES.get('cart')

            if cart_str:

                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

            if sku_id in cart_dict:
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }

            cookie_cart = base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 返回

            response = Response(serializer.data)
            response.set_cookie('cart', cookie_cart)

            return response

    def delete(self, request):
        """删除"""
        # 检查参数sku_id
        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data['sku_id']

        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            # 前端携带了错误的 JWT  用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 如果用户登录，修改redis数据
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, sku_id)
            pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(status=status.HTTP_204_NO_CONTENT)

        else:
            # cookie
            cart_str = request.COOKIES.get('cart')

            if cart_str:

                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

            response = Response(serializer.data)

            if sku_id in cart_dict:
                # 删除字典的键值对
                del cart_dict[sku_id]

                cookie_cart = base64.b64encode(pickle.dumps(cart_dict)).decode()

                response.set_cookie('cart', cookie_cart)

            return response





























