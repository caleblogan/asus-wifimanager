from django.db import models


class Client(models.Model):
    mac_addr = models.CharField(max_length=17, primary_key=True)
    name = models.CharField(max_length=200)
    name_alias = models.CharField(max_length=200, default='')
    ip_addr = models.CharField(max_length=15)
    is_blocked = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.mac_addr} ({self.ip_addr})'


# class ConnectionSample(models.Model):
#     """Represents a clients connection info at a point in time"""
#     client = models.ForeignKey(Client, on_delete=models.CASCADE)
#     tx = models.
