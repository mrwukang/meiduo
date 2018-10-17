from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from areas import views

urlpatterns = [
    # url(r'^infos/$', views.AreaView.as_view(), name="province"),
    # url(r'^infos/(?P<pk>\d+)/$', views.AreaSubsView.as_view(), name="city"),

]
router = DefaultRouter()
router.register(r'infos', views.AreaViewSet, base_name="areas")
urlpatterns += router.urls
