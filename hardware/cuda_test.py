import os
import sys
import glob
from influxdb import InfluxDBClient

INFLUX_HOST = "172.18.65.10"
# influxdb 端口(int)
# INFLUX_PORT = 12003
INFLUX_PORT = 8086
# influxdb 用户名
INFLUX_USER = "collect"
# influxdb 密码
INFLUX_PASSWORD = "collect@123"
# influxdb 数据库
INFLUX_DATABASE = "gpu_test"


def connect_influxdb():
    # client = InfluxDBClient(host='69.194.1.66', port=12003, username='monitor', password='qtum7886',database='collectd', timeout=5)
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, username=INFLUX_USER, password=INFLUX_PASSWORD, database=INFLUX_DATABASE, timeout=5)
    return client


def insert_influxdb(client, json_body):
    client.write_points(json_body)


def query_influxdb(client, sql):
    data = client.query(sql)
    return data


# Connect to InfluxDB
client = connect_influxdb()


# Function to read and insert data from files
def insert_data_from_files():

    # Find all gpu_metrics files
    files = glob.glob("gpu_metrics*.txt")

    for file in files:
        with open(file, 'r') as f:
            for line in f:
                # Parse the line
                parts = line.strip().split(' ')
                tags, fields, timestamp = parts[0], parts[1], parts[2]

                # Extract tag values
                tag_parts = tags.split(',')
                host = tag_parts[1].split('=')[1]
                gpu = int(tag_parts[2].split('=')[1])

                # Extract field values
                field_parts = fields.split(',')
                temp = float(field_parts[0].split('=')[1])
                clock_speed = float(field_parts[1].split('=')[1])
                power = float(field_parts[2].split('=')[1])

                # Create a point and write to InfluxDB
                # point = Point("cuda_result") \
                #     .tag("host", host) \
                #     .tag("gpu", gpu) \
                #     .field("temp", temp) \
                #     .field("clock_speed", clock_speed) \
                #     .field("power", power) \
                #     .time(int(timestamp))
                #
                # write_api.write(bucket=bucket, org=org, record=point)
                # print(f"Inserted data from {file}: {line.strip()}")

                json_body = [
                    {
                        "measurement": "hardware",
                        "tags": {
                            "gpu_id": gpu,
                            "host": host,
                        },
                        "fields": {
                            "temp": temp,
                            "clock_speed": clock_speed,
                            "power": power,
                            "time": int(timestamp),
                        }
                    }
                ]
                insert_influxdb(client, json_body)


# Run the data insertion
insert_data_from_files()

# Close the client
client.close()