"""mall URL Configuration

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
from rest_framework.documentation import include_docs_urls
# import xadmin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # url(r'xadmin/', include(xadmin.site.urls)),
    url(r'^users/', include('users.urls', namespace="users")),
    url(r'^oauth/', include('oauth.urls', namespace="oauth")),
    url(r'^verifications/', include('verifications.urls', namespace="verifications")),
    url(r'^areas/', include('areas.urls', namespace="areas")),
    url(r'^goods/', include('goods.urls', namespace="goods")),
    url(r'^ckeditor/', include('ckeditor_uploader.urls'), name="ckeditor"),
    url(r'^cart/', include('carts.urls', namespace='cart')),
    url(r'^orders/', include('orders.urls', namespace='orders')),
    url(r'^docs/', include_docs_urls(title='API接口文档')),

]
