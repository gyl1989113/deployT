import json
import os
import re
import socket
import sys
import glob
from influxdb import InfluxDBClient

INFLUX_HOST = "172.18.65.10"
INFLUX_PORT = 8086
INFLUX_USER = "collect"
INFLUX_PASSWORD = "collect@123"
INFLUX_DATABASE = "gpu_test"
MEASUREMENT = sys.argv[1]
if MEASUREMENT == "":
    print("Please provide a measurement name as the first argument.")
    sys.exit(1)


def connect_influxdb():
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, username=INFLUX_USER, password=INFLUX_PASSWORD, database=INFLUX_DATABASE, timeout=5)
    return client


def insert_influxdb(client, json_body):
    client.write_points(json_body)


def query_influxdb(client, sql):
    data = client.query(sql)
    return data


# Function to read and insert data from files
def insert_data_from_files():
    # Connect to InfluxDB
    client = connect_influxdb()
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
                        "measurement": MEASUREMENT,
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

    # Close the client
    client.close()


def get_basic_info():

    gpu_info_map = {
        "NVIDIA GeForce RTX 2080": {
            "sm_count": 68,
            "cuda_cores": 2944,
            "l2_cache_size": 4
        },
        "NVIDIA GeForce RTX 2080 Ti": {
            "sm_count": 72,
            "cuda_cores": 4352,
            "l2_cache_size": 6
        },
        "NVIDIA GeForce RTX 3080": {
            "sm_count": 68,
            "cuda_cores": 8704,
            "l2_cache_size": 5
        },
        "NVIDIA GeForce RTX 3090": {
            "sm_count": 82,
            "cuda_cores": 10496,
            "l2_cache_size": 6
        },
        "NVIDIA GeForce RTX 4080": {
            "sm_count": 76,
            "cuda_cores": 9728,
            "l2_cache_size": 6
        },
        "NVIDIA GeForce RTX 4090": {
            "sm_count": 128,
            "cuda_cores": 16384,
            "l2_cache_size": 10
        }
    }

    """获取CPU型号和核心数."""
    with open('/proc/cpuinfo') as f:
        for line in f:
            if line.strip().startswith('model name'):
                cpu_model = re.search(r':\s*(.*)', line).group(1)
                break
    # 获取核心数
    try:
        cpu_cores = os.cpu_count()
    except AttributeError:
        cpu_cores = None  # 某些系统可能无法获取核心数

    # 发行版本
    release = os.popen('cat /etc/issue').read().strip().split('\n')[0]
    # 内核
    kernel = os.popen('uname -r').read().strip()
    # 主机名
    hostname = socket.gethostname()
    # 显卡驱动版本
    driver_version = os.popen('nvidia-smi -q | grep "Driver Version"').read().strip().split(': ')[1]
    # 显卡型号
    gpu_model = os.popen('nvidia-smi --query-gpu=name --format=csv,noheader').read().strip()
    if '\n' in gpu_model:
        gpu_model = gpu_model.split('\n')[0]
    if gpu_model in gpu_info_map:
        info = gpu_info_map[gpu_model]
        gpu_sm_count = info['sm_count']
        gpu_cuda_cores = info['cuda_cores']
        gpu_l2_cache_size = info['l2_cache_size']
    else:
        gpu_sm_count = 0
        gpu_cuda_cores = 0
        gpu_l2_cache_size = 0

    # CUDA Version
    cuda_version = os.popen("nvidia-smi -x -q | grep cuda | sed 's/<[^>]*>//g' | tr -d '[:space:]'").read().strip()

    basic_info = {'hostname': hostname, 'release': release, 'kernel': kernel, 'driver_version': driver_version,
                    'gpu_model': gpu_model, 'cuda_version': cuda_version, 'cpu_model': cpu_model, 'cpu_cores': cpu_cores,
                    'gpu_sm_count': gpu_sm_count, 'gpu_cuda_cores': gpu_cuda_cores, 'gpu_l2_cache_size': gpu_l2_cache_size}

    # 将 basic_info 写入 JSON 文件
    with open('base_info.json', 'w') as json_file:
        json.dump(basic_info, json_file, indent=4)  # 使用 indent=4 使输出格式化


if __name__ == '__main__':
    # Run the data insertion
    insert_data_from_files()
    # leave a json file for basic info
    get_basic_info()

