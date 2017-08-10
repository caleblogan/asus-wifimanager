from django.db import models
from django.utils import timezone

import datetime


class Client(models.Model):
    mac_addr = models.CharField(max_length=17, primary_key=True)
    name = models.CharField(max_length=200, default='not set')
    name_alias = models.CharField(max_length=200, default='')
    ip_addr = models.CharField(max_length=15, default='')
    is_blocked = models.BooleanField(default=False)

    def update_from_asus_client(self, asus_client):
        self.mac_addr = asus_client.mac_addr
        self.name = asus_client.name
        self.ip_addr = asus_client.ip_addr
        self.is_blocked = asus_client.is_blocked

    def compare_to_asus_client(self, asus_client):
        return (self.mac_addr == asus_client.mac_addr and
                self.name == asus_client.name and
                self.ip_addr == asus_client.ip_addr and
                self.is_blocked == asus_client.is_blocked)

    @classmethod
    def get_currently_connnected_clients(cls):
        connection_samples = ConnectionSample.objects.filter(time_of_sample__gt=timezone.now()-datetime.timedelta(minutes=4))
        clients = [sample.client for sample in connection_samples.distinct('client')]
        for client in clients:
            client.mac_addr_safe = client.mac_addr.replace(':', '_')
        return clients

    def __str__(self):
        return f'{self.mac_addr} ({self.ip_addr})'


class ConnectionSample(models.Model):
    """Represents a clients connection info at a point in time"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    tx = models.FloatField()
    rx = models.FloatField()
    rssi = models.CharField('signal strength', max_length=15)
    connection_time = models.CharField(max_length=15)
    time_of_sample = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.client} (tx={self.tx} rx={self.rx} connection_time={self.connection_time})'
