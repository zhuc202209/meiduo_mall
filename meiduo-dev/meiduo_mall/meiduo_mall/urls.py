"""meiduo_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url, include
from django.contrib import admin
# import xadmin
from rest_framework.documentation import include_docs_urls
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.schemas import get_schema_view
# 导入两个类
from rest_framework_swagger.renderers import SwaggerUIRenderer,OpenAPIRenderer
from rest_framework.schemas import get_schema_view
# 导入两个类
from rest_framework_swagger.renderers import SwaggerUIRenderer,OpenAPIRenderer
 
 # 利用辅助函数引入所导入的两个类
schema_view = get_schema_view(title='API',renderer_classes=[SwaggerUIRenderer,OpenAPIRenderer])
 

 
urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    # url(r'xadmin/', include(xadmin.site.urls)),
    url(r'^', include('verifications.urls')),
    url(r'^', include('users.urls')),
    url(r'oauth/', include('oauth.urls')),
    url(r'', include('areas.urls')),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^', include('goods.urls')),
    url(r'^', include('carts.urls')),
    url(r'^', include('orders.urls')),
    url(r'^', include('payment.urls')),  
    url(r'^docs/', include_docs_urls(title='restframwork接口文档')),
    url('^swagger/',schema_view,name='swagger')   # 配置docs的url路径
    # url(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    # url(r"^swagger/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    # url(r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
