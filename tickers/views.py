from django.utils.dateparse import parse_datetime
from rest_framework import generics

from .models import TickerPrice
from .serializers import TickerPriceSerializer


class TickerPriceListView(generics.ListAPIView):
    serializer_class = TickerPriceSerializer

    def get_queryset(self):
        queryset = TickerPrice.objects.all()
        symbol = self.request.query_params.get('symbol')
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        if symbol:
            queryset = queryset.filter(symbol__iexact=symbol)
        if start:
            dt_start = parse_datetime(start)
            if dt_start:
                queryset = queryset.filter(event_time__gte=dt_start)
        if end:
            dt_end = parse_datetime(end)
            if dt_end:
                queryset = queryset.filter(event_time__lte=dt_end)
        return queryset.order_by('-event_time')
