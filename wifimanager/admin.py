from django.contrib import admin

from .models import Client, ConnectionSample


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('mac_addr', 'name', 'name_alias', 'ip_addr', 'is_blocked')


admin.site.register(ConnectionSample)
