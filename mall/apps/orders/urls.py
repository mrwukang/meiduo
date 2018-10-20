from django.conf.urls import url
from orders import views

urlpatterns = [
    url(r'^places/$', views.OrderSettlementView.as_view(), name='placeorder'),
    url(r'^$', views.OrderView.as_view(), name='commitorder'),
]

