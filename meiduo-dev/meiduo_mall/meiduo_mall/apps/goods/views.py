from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework_extensions.cache.mixins import ListCacheResponseMixin
from rest_framework.filters import OrderingFilter
from drf_haystack.viewsets import HaystackViewSet

from .serializers import SKUSerializer, SKUIndexSerializer
from .models import SKU
from . import constants

# Create your views here.


class HotSKUListView(ListCacheResponseMixin, ListAPIView):
    """返回热销数据
    /categories/(?P<category_id>\d+)/hotskus/
    """
    serializer_class = SKUSerializer
    pagination_class = None

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:constants.HOT_SKUS_COUNT_LIMIT]


class SKUListView(ListAPIView):
    """
    商品列表数据
    /categories/(?P<category_id>\d+)/skus?page=xxx&page_size=xxx&ordering=xxx
    """
    serializer_class = SKUSerializer

    # 通过定义过滤后端 ，来实行排序行为
    filter_backends = [OrderingFilter]
    ordering_fields = ('create_time', 'price', 'sales')

    def get_queryset(self):
        categroy_id = self.kwargs.get("category_id")
        return SKU.objects.filter(category_id=categroy_id, is_launched=True)


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]

    serializer_class = SKUIndexSerializer