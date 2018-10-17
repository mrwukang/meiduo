from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
# Create your views here.
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from areas.models import Area
from areas.serializers import AreaSerializer, AreaSubsSerializers


# class AreaView(ListAPIView):
#     """
#     GET:   /areas/infos/
#     """
#     pagination_class = None
#     queryset = Area.objects.filter(parent=None)
#     serializer_class = AreaSerializer
#
#
# class AreaSubsView(RetrieveAPIView):
#     """
#     GET:   /areas/infos/(?P<pk>\d+)/
#     """
#     pagination_class = None
#     queryset = Area.objects.all()
#     serializer_class = AreaSubsSerializers

class AreaViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    """使用视图集，这样必须重写get_queryset和get_serializer_class方法"""
    pagination_class = None

    def get_queryset(self):
        if self.action == 'list':
            return Area.objects.filter(parent__isnull=True)
        else:
            return Area.objects.all()

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "list":
            return AreaSerializer
        else:
            return AreaSubsSerializers


