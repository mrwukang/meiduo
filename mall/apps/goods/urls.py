from django.conf.urls import url
from goods import views

urlpatterns = [
    url(r'categories/$', views.CategoryView.as_view(), name='categories'),
    url(r'categories/(?P<category_id>\d+)/hotskus/$', views.HotSKUListView.as_view(), name='hotsku'),
    url(r'categories/(?P<category_id>\d+)/skus/$', views.SKUListView.as_view(), name='sku'),
]
