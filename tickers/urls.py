from django.urls import path
from . import views

urlpatterns = [
    path(
        'tickers/',
        views.TickerPriceListView.as_view(),
        name='tickerprice-list'
    ),
    # path('', TemplateView.as_view(template_name='tickers.html'), name='tickers-test'),
]
