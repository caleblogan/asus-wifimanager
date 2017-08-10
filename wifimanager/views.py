from django.shortcuts import render
from .asus_router import AsusApi
from django.db import models
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.utils import timezone

import datetime

from .models import Client, ConnectionSample


def index(request):
    remote_addr = request.META['REMOTE_ADDR']

    # hack to get around my two wifi interfaces not working with ui quite right
    user_ip_addr = '192.168.1.53' if remote_addr  == '192.168.1.192' else remote_addr
    context = {
        'clients': Client.get_currently_connnected_clients(),
        'user_ip_addr': user_ip_addr,
    }
    return render(request, 'wifimanager/index.html', context=context)


@csrf_exempt
def update_client_name_alias(request):
    mac_addr = request.POST['mac_addr']
    new_name_alias = request.POST['new_name_alias']
    try:
        client = Client.objects.get(pk=mac_addr)
        client.name_alias = new_name_alias
        client.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': e})


def get_connection_samples(request):
    """Gets the connections samples from the db in the range of now-dt"""
    dt = request.GET['dt']
    connection_samples = ConnectionSample.objects.filter(time_of_sample__gt=timezone.now()-datetime.timedelta(minutes=float(dt)))
    client_samples = group_by('client.mac_addr', connection_samples)
    json_client_samples = {}
    for mac, samples in client_samples.items():
        mac = mac.replace(':', '_')
        json_client_samples[mac] = [model_to_dict(m) for m in samples]
    return JsonResponse({'success': True, 'client_samples': json_client_samples})


@csrf_exempt
def update_connected_clients(request):
    """Gets the connected clients from the asus router and updates the db"""
    api = AsusApi()
    asus_clients = api.get_connected_clients()
    for asus_client in asus_clients:
        try:
            client = Client.objects.get(pk=asus_client.mac_addr)
            if not client.compare_to_asus_client(asus_client):
                client.update_from_asus_client(asus_client)
                client.save()
                print(f'{client} ---------- not equal -----------')
        except models.ObjectDoesNotExist as e:
            client = Client(mac_addr=asus_client.mac_addr, name=asus_client.name,
                            ip_addr=asus_client.ip_addr, is_blocked=asus_client.is_blocked)
            client.save()
    return JsonResponse({'success': True})


# @require_POST
@csrf_exempt
def collect_connection_samples(request):
    """Gets the connection info for current clients at the moment in time and adds them to the db"""
    api = AsusApi()
    try:
        asus_connection_samples = api.get_client_connection_statuses()
    except Exception as e:
        api.login()
        asus_connection_samples = api.get_client_connection_statuses()
    new_samples = []
    for asus_sample in asus_connection_samples:
        try:
            client = Client.objects.get(pk=asus_sample.mac_addr)
        except Exception as e:
            client = Client(mac_addr=asus_sample.mac_addr)
            client.save()
        new_sample = ConnectionSample(client=client, tx=asus_sample.tx_rate, rx=asus_sample.rx_rate,
                                      rssi=asus_sample.rssi, connection_time=asus_sample.connection_time)
        new_sample.save()
        new_samples.append(new_sample)
    return JsonResponse({'success': True, 'samples': [model_to_dict(m) for m in new_samples]},)


@csrf_exempt
def remove_old_connection_samples(request):
    try:
        deleted_samples = ConnectionSample.objects.filter(
                                                        time_of_sample__lt=timezone.now()-datetime.timedelta(minutes=5)
                                                    ).delete()
        return JsonResponse({'samples_removed': deleted_samples[0]})
    except Exception as e:
        return JsonResponse({'error': 'failed to remove connection samples'})


# ----------- Utils --------------

def get_field(row, field):
    """Gets the field of a queryobject by reference. Will get subfields as well eg. client.mac_addr or client"""
    sub_fields = field.split('.')
    for sub_field in sub_fields:
        row = getattr(row, sub_field)
    return row


def group_by(field, query_set):
    """Groups by a field eg. ConnectionSample.client. Returns a dict of field: [queryobjects...]"""
    groups = {}
    for row in query_set:
        if get_field(row, field) not in groups:
            groups[get_field(row, field)] = []
        groups[get_field(row, field)].append(row)
    return groups

