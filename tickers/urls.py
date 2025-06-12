from django.urls import path
from . import views

urlpatterns = [
    path(
        'tickers/',
        views.TickerPriceListView.as_view(),
        name='tickerprice-list'
    ),
    path(
        'tickers/history/',
        views.TickerPriceHistoryView.as_view(),
        name='tickerprice-history'
    ),
]
