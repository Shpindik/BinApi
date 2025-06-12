import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timezone as dt_timezone
from rest_framework import status
from rest_framework.test import APIClient
from decimal import Decimal

from tickers.models import TickerPrice


@pytest.mark.django_db
class TestTickerPriceListView:
    """Тесты для представления списка цен тикеров"""
    def setup_method(self):
        '''Настройка клиента API и очистка базы данных перед каждым тестом'''
        self.client = APIClient()
        self.url = reverse('tickerprice-list')
        self.now = timezone.now()
        # Очистка базы данных перед каждым тестом
        TickerPrice.objects.all().delete()

    def test_list_tickers(self):
        '''Тест получения списка всех тикеров'''
        TickerPrice.objects.create(
            symbol='BTCUSDT',
            price='50000.00',
            event_time=self.now
        )
        TickerPrice.objects.create(
            symbol='ETHUSDT',
            price='3000.00',
            event_time=self.now
        )

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_filter_by_symbol(self):
        '''Тест фильтрации тикеров по символу'''
        TickerPrice.objects.create(
            symbol='BTCUSDT',
            price='50000.00',
            event_time=self.now
        )
        TickerPrice.objects.create(
            symbol='BTCUSDT',
            price='51000.00',
            event_time=self.now + timezone.timedelta(seconds=10)
        )
        TickerPrice.objects.create(
            symbol='ETHUSDT',
            price='3000.00',
            event_time=self.now
        )

        response = self.client.get(f"{self.url}?symbol=BTCUSDT")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['symbol'] == 'BTCUSDT'
        assert response.data[0]['price'] == '51000.00000000'

    def test_filter_by_time_range(self):
        '''Тест фильтрации тикеров по диапазону времени'''
        # Создание тестовых данных с явной временной зоной
        now = timezone.now()
        TickerPrice.objects.create(
            symbol='BTCUSDT',
            price=Decimal('50000.00'),
            event_time=now.replace(tzinfo=dt_timezone.utc)
        )
        TickerPrice.objects.create(
            symbol='ETHUSDT',
            price=Decimal('3000.00'),
            event_time=now.replace(tzinfo=dt_timezone.utc)
        )

        # Тест фильтрации по диапазону времени
        start_time = now.replace(tzinfo=dt_timezone.utc)
        end_time = now.replace(tzinfo=dt_timezone.utc)
        url = reverse('tickerprice-list')
        response = self.client.get(
            f'{url}?start_time={start_time.isoformat()}&'
            f'end_time={end_time.isoformat()}'
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Оба тикера должны быть включены
