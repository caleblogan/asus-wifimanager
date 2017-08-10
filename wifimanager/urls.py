from django.conf.urls import url

from . import views

app_name = 'wifimanager'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^update_connected_clients/$', views.update_connected_clients, name='update-connected-clients'),
    url(r'^collect_connection_samples/$', views.collect_connection_samples, name='collect-connection-samples'),
    url(r'^remove_old_connection_samples/$', views.remove_old_connection_samples, name='remove-old-connection-samples'),
    url(r'^connection_samples/$', views.get_connection_samples, name='get-connection-samples'),
    url(r'^update_client_name_alias/$', views.update_client_name_alias, name='update-client-name-alias'),
]
