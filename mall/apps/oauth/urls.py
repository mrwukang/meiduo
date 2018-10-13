from django.conf.urls import url
from oauth import views

urlpatterns = [
    url(r'^qq/authorization/$', views.QQAuthURLView.as_view(), name='qqauthurl'),
    url(r'^qq/user/$', views.QQAuthUserView.as_view(), name='qqauthuser'),
]
