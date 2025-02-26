import os
import sys
import glob
from influxdb import InfluxDBClient

INFLUX_HOST = "172.18.65.10"
INFLUX_PORT = 8086
INFLUX_USER = "collect"
INFLUX_PASSWORD = "collect@123"
INFLUX_DATABASE = "gpu_test"


def connect_influxdb():
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
                json_body = [
                    {
                        "measurement": "cuda_result",
                        "tags": {
                            "gpu_id": gpu,
                            "host": host,
                        },
                        "fields": {
                            "temp": temp,
                            "clock_speed": clock_speed,
                            "power": power,
                        },
                        "time": int(timestamp)  # Set the timestamp here
                    }
                ]
                insert_influxdb(client, json_body)


# Run the data insertion
insert_data_from_files()

# Close the client
client.close()