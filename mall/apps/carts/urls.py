from django.conf.urls import url
from carts import views

urlpatterns = [
    url(r"^$", views.CartView.as_view(), name='cart')
]
