# Used to collect connection samples from a asus router and store them in the db that the client app is using.
import time
import requests
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Asus Router Connection Sample Collector.')
    print('Collection Samples Collector. Pres ctrl-c to stop.')
    print('Now collecting samples...')
    while True:
        try:
            res = requests.post('http://127.0.0.1:8000/dashboard/collect_connection_samples/')
            print(f'Res: {res.status_code}  Samples collected: {len(res.json()["samples"])}')
            requests.post('http://127.0.0.1:8000/dashboard/remove_old_connection_samples/')
            requests.post('http://127.0.0.1:8000/dashboard/update_connected_clients/')
            time.sleep(2)
        except Exception as e:
            print(e)
            time.sleep(5)
