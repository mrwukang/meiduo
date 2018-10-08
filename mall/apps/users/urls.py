from django.conf.urls import url
from users import views

urlpatterns = [
    url(r'usernames/(?P<username>\w{5,20})/count/', views.RegisterUsernameAPIView.as_view(), name="usernamecount"),
    url(r'phones/(?P<mobile>1[3456789]\d{9})/count/', views.RegisterPhoneCountAPIView.as_view(), name="phonecount"),
    url(r'^$', views.RegisterCreateView.as_view(), name="register"),

]
