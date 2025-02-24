import os
import sys
import glob
local_path = os.getcwd()
o_path = os.path.abspath(os.path.join(local_path, "../"))  # 返回当前工作目录
sys.path.append(o_path)
from tools.tools import *


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