import base64
import pickle

from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, response, user):
    """
    合并购物车，cookie保存到redis中
    :return: 
    """
    # 从cookie中取出购物车数据
    cart_str = request.COOKIES.get('cart')

    if not cart_str:
        return response

    cookie_cart = pickle.loads(base64.b64decode(cart_str.encode()))

    # {
    #     sku_id: {
    #                 "count": xxx, // 数量
    #             "selected": True // 是否勾选
        # },
        # sku_id: {
        #     "count": xxx,
        #     "selected": False
        # },
        # ...
    # }

    # 从redis中取出购物车数据
    redis_conn = get_redis_connection('cart')
    cart_redis = redis_conn.hgetall('cart_%s' % user.id)
    # 把redis取出的字典的键值对数据类型 转换为int

    cart = {}
    for sku_id, count in cart_redis.items():
        cart[int(sku_id)] = int(count)

    # {
    #     sku_id: count,
    #     sku_id: count
    # }

    selected_sku_id_list = []
    for sku_id, selected_count_dict in cookie_cart.items():
        # 如果redis购物车中原有商品数据，数量覆盖，如果没有，新添记录
        cart[sku_id] = selected_count_dict['count']

        # 处理勾选状态，
        if selected_count_dict['selected']:
            selected_sku_id_list.append(sku_id)

    # 将cookie的购物车合并到redis中
    pl = redis_conn.pipeline()
    pl.hmset('cart_%s' % user.id, cart)

    #     selected_sku_id_list = [1,2,3,4,]
    # pl.sadd('cart_selected_%s' % user.id, 1, 2, 3, 4)
    pl.sadd('cart_selected_%s' % user.id, *selected_sku_id_list)

    pl.execute()

    # 清除cookie中的购物车数据
    response.delete_cookie('cart')

    return response
