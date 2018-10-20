from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from users import views
from rest_framework_jwt.views import obtain_jwt_token


urlpatterns = [
    url(r'usernames/(?P<username>\w{5,20})/count/', views.RegisterUsernameAPIView.as_view(), name="usernamecount"),
    url(r'phones/(?P<mobile>1[3-9]\d{9})/count/', views.RegisterPhoneCountAPIView.as_view(), name="phonecount"),
    url(r'^$', views.RegisterCreateView.as_view(), name="register"),
    url(r'^auths/', views.UserAuthorizationView.as_view(), name='auths'),
    url(r'^infos/', views.UserDetailView.as_view(), name='infos'),
    url(r'^emails/$', views.EmailView.as_view(), name='send_email'),
    url(r'^emails/verification/$', views.VerificationEmail.as_view(), name='verification_email'),
    url(r'^browerhistories/$', views.UserBrowsingHistoryView.as_view(), name='browsing_history'),

]
from users.views import AddressViewSet
router = DefaultRouter()
router.register(r'addresses', AddressViewSet, base_name='address')
urlpatterns += router.urls
