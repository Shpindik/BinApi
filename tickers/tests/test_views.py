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
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('tickerprice-list')
        self.now = timezone.now()
        # Clear database before each test
        TickerPrice.objects.all().delete()

    def test_list_tickers(self):
        """Test listing all tickers"""
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
        """Test filtering tickers by symbol"""
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

        response = self.client.get(f"{self.url}?symbol=BTCUSDT")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['symbol'] == 'BTCUSDT'

    def test_filter_by_time_range(self):
        """Test filtering tickers by time range"""
        # Create test data with explicit timezone
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

        # Test filtering by time range
        start_time = now.replace(tzinfo=dt_timezone.utc)
        end_time = now.replace(tzinfo=dt_timezone.utc)
        url = reverse('tickerprice-list')
        response = self.client.get(
            f'{url}?start_time={start_time.isoformat()}&end_time={end_time.isoformat()}'
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Both tickers should be included 