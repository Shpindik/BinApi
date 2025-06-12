from django.db import models


class TickerPrice(models.Model):
    """Модель для хранения цен тикеров"""
    symbol = models.CharField(max_length=20, db_index=True)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    event_time = models.DateTimeField(db_index=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-event_time']
        indexes = [
            models.Index(fields=['symbol', 'event_time']),
        ]

    def __str__(self):
        return f"{self.symbol}: {self.price} @ {self.event_time}"
