import socket
import time
import os
import sys

from influxdb import InfluxDBClient
local_path = os.getcwd()
o_path = os.path.abspath(os.path.join(local_path, ".."))  # 返回当前工作目录
sys.path.append(o_path)
from tools.__config import *

filter_list = ['temp', 'product', 'speed', 'uuid', 'gpu', 'driver']


def connect_influxdb():
    # client = InfluxDBClient(host='69.194.1.66', port=12003, username='monitor', password='qtum7886',database='collectd', timeout=5)
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, username=INFLUX_USER, password=INFLUX_PASSWORD, database=INFLUX_DATABASE, timeout=5)
    return client


def insert_influxdb(client, json_body):
    client.write_points(json_body)


def query_influxdb(client, sql):
    data = client.query(sql)
    return data


def parse_xml_to_json(xml):
    response = {}
    for child in list(xml):
        flag = False
        for filter in filter_list:
            if filter in child.tag:
                flag = True
                break
        if not flag:
            continue
        if len(list(child)) > 0:
            if not response.get(child.tag):
                response[child.tag] = []
            response[child.tag].append(parse_xml_to_json(child))
        elif child.text.strip() != 'N/A' and child.text.strip() != '':
            response[child.tag] = child.text.strip()

        if type(response.get(child.tag)) is dict and len(response.get(child.tag)) == 0:
            del response[child.tag]
        if type(response.get(child.tag)) is list and len(response.get(child.tag)) == 0:
            del response[child.tag]
        if type(response.get(child.tag)) is list and len(response.get(child.tag)) == 1 and len(
                response.get(child.tag)[0]) == 0:
            del response[child.tag]
    return response


if __name__ == '__main__':
    client = connect_influxdb()
    json_body = [
        {
            "measurement": "mpool_mysql",
            "tags": {
                "timestamp": int(time.time())
            },
            "fields": {
                "host": socket.gethostname(),
                "Threads_connected": 2,
                "tps": 1.1,
                "qps": 2.2,
                "slave_status": "error"
            }
        }
    ]
    insert_influxdb(client, json_body)
    client.close()