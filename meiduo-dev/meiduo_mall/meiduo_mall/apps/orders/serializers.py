from django_redis import get_redis_connection
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal

from carts.serializers import CartSKUSerializer
from .models import OrderInfo, OrderGoods
from django.utils import timezone
from goods.models import SKU


class OrderSettlementSerializer(serializers.Serializer):
    # max_digits 包含小数的最多位数，decimal_places 几位小数
    freight = serializers.DecimalField(max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True, read_only=True)


class SaveOrderSerializer(serializers.ModelSerializer):
    """保存订单的序列化器"""
    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')

        # 'write_only':   向后端写数据  向后端传数据
        # 'read_only':  前端要从后端读取数据，后端返回数据使用
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        """保存订单"""
        # 获取当前下单用户
        user = self.context['request'].user

        # 保存订单的基本信息数据 OrderInfo
        # 创建订单编号
        # 20180523160505+ user_id  100
        # timezone.now() -> datetime
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        address = validated_data['address']
        pay_method = validated_data['pay_method']

        # 开启事务
        with transaction.atomic():
            # 创建保存点，记录当前数据状态
            save_id = transaction.savepoint()

            try:
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.0'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method==OrderInfo.PAY_METHODS_ENUM['CASH'] else OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )

                # 从redis中获取购物车数据
                redis_conn = get_redis_connection('cart')
                cart_redis = redis_conn.hgetall('cart_%s' % user.id)
                cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

                cart = {}
                # cart: {
                # sku_id: count,
                # sku_id: count
                # }
                for sku_id in cart_selected:
                    cart[int(sku_id)] = int(cart_redis[sku_id])

                # sku_obj_list = SKU.objects.filter(id__in=cart.keys())
                sku_id_list = cart.keys()
                # 遍历勾选要下单的商品数据，
                for sku_id in sku_id_list:
                    while True:
                        sku = SKU.objects.get(id=sku_id)

                        # 判断商品库存是否充足
                        count = cart[sku.id]
                        origin_stock = sku.stock
                        print('origin_stock=%s' % origin_stock)
                        origin_sales = sku.sales

                        if sku.stock < count:
                            # 事务回滚
                            transaction.savepoint_rollback(save_id)
                            raise serializers.ValidationError('商品库存不足')

                        # import time
                        # time.sleep(5)

                        # 减少商品的库存 SKU
                        # sku.stock -= count
                        # sku.sales += count
                        # sku.save()
                        new_stock = origin_stock - count
                        new_sales = origin_sales + count

                        # 返回受影响的行数
                        ret = SKU.objects.filter(id=sku.id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                        if ret == 0:
                            continue

                        order.total_count += count
                        order.total_amount += (sku.price * count)

                        # 保存到OrderGoods
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=count,
                            price=sku.price,
                        )

                        break

                # 更新订单的数量与金额信息
                order.save()
            except serializers.ValidationError:
                raise

            except Exception:
                transaction.savepoint_rollback(save_id)
                raise

            # 提交事务
            transaction.savepoint_commit(save_id)

            # 清除购物车中已经结算的商品
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, *cart_selected)
            pl.srem('cart_selected_%s' % user.id, *cart_selected)
            pl.execute()

            return order






















