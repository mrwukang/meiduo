from django.shortcuts import render

# Create your views here.
from rest_framework.generics import ListAPIView, RetrieveAPIView

from areas.models import Area
from areas.serializers import AreaSerializer, AreaSubsSerializers


class AreaView(ListAPIView):
    """
    GET:   /areas/infos/
    """
    pagination_class = None
    queryset = Area.objects.filter(parent=None)
    serializer_class = AreaSerializer


class AreaSubsView(RetrieveAPIView):
    """
    GET:   /areas/infos/(?P<pk>\d+)/
    """
    pagination_class = None
    queryset = Area.objects.all()
    serializer_class = AreaSubsSerializers

