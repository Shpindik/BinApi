import pytest
from django.utils import timezone
from datetime import timezone as dt_timezone
from tickers.models import TickerPrice


@pytest.mark.django_db
class TestTickerPrice:
    """Тесты для модели TickerPrice"""
    def test_create_ticker(self):
        '''Тест создания новой цены тикера'''
        ticker = TickerPrice.objects.create(
            symbol='BTCUSDT',
            price='50000.00',
            event_time=timezone.now()
        )
        assert ticker.symbol == 'BTCUSDT'
        assert ticker.price == '50000.00'
        assert ticker.received_at is not None

    def test_ticker_str_representation(self):
        '''Тест строкового представления тикера'''
        now = timezone.now()
        ticker = TickerPrice.objects.create(
            symbol='ETHUSDT',
            price='3000.00',
            event_time=now
        )
        expected_str = f'ETHUSDT: 3000.00 @ {now}'
        assert str(ticker) == expected_str

    def test_ticker_ordering(self):
        '''Тест сортировки тикеров по умолчанию'''
        now = timezone.now()
        old_time = now - timezone.timedelta(hours=1)

        # Создание тикеров с явным указанием временной зоны
        TickerPrice.objects.create(
            symbol='BTCUSDT',
            price='50000.00',
            event_time=now.replace(tzinfo=dt_timezone.utc)
        )
        TickerPrice.objects.create(
            symbol='BTCUSDT',
            price='49000.00',
            event_time=old_time.replace(tzinfo=dt_timezone.utc)
        )

        tickers = TickerPrice.objects.all()
        assert (
            tickers[0].event_time == now.replace(tzinfo=dt_timezone.utc)
        )
        assert (
            tickers[1].event_time == old_time.replace(tzinfo=dt_timezone.utc)
        )
