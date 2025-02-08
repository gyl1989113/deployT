import os
import sys
import re
import time
import socket
import psutil
from xml.etree import ElementTree as ET
local_path = os.getcwd()
o_path = os.path.abspath(os.path.join(local_path, "../"))  # 返回当前工作目录
sys.path.append(o_path)
from tools.tools import *
import subprocess


def gpu_data():
    cmd = 'nvidia-smi -x -q'
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().strip()
    except subprocess.CalledProcessError as e:
        error_output = e.output.decode().strip()
        # 显卡错误
        if "Unknown Error" in error_output or "failed" in error_output:
            print("{} :gpu failed,please check".format(socket.gethostname()))
            return [{'gpu_status': 2, 'fan_speed': '0', 'temp': '0', 'frequency': '0', 'power': '0'}]
        # 没有显卡
        if "not found" in error_output:
            return [{'gpu_status': 0, 'fan_speed': '0', 'temp': '0', 'frequency': '0', 'power': '0'}]

    gpu_infos = list()
    xml = ET.XML(result)
    info = parse_xml_to_json(xml)
    for gpu in info.get('gpu'):
        gpu_info = {
            'gpu_status': 1,
            'fan_speed': gpu.get('fan_speed'),
            'temp': gpu.get('temperature')[0].get('gpu_temp'),
            'frequency': gpu.get('clocks')[0].get('graphics_clock'),  # Get the graphics frequency
            'power': gpu.get('gpu_power_readings')[0].get('power_draw'),  # Get the power usage
        }
        gpu_infos.append(gpu_info)
    return gpu_infos


# 基础指标
def basic_info():
    # 发行版本
    release = os.popen('cat /etc/issue').read().strip()
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
    # CUDA Version
    cuda_version = os.popen("nvidia-smi -x -q | grep cuda | sed 's/<[^>]*>//g' | tr -d '[:space:]'").read().strip()
    # cpu使用率
    cpu_util_all = psutil.cpu_percent(interval=1, percpu=True)
    cpu_utils = sum(cpu_util_all)/len(cpu_util_all)
    cpu_utils = "{:.2f}".format(cpu_utils)
    # 内存使用率
    mem = psutil.virtual_memory()
    mem_utils = (mem.total-mem.free)/mem.total
    mem_utils = "{:.2f}".format(mem_utils)
    # cpu 频率
    cpu_freq = psutil.cpu_freq().current

    basic_metrics = {'hostname': hostname, 'release': release, 'kernel': kernel, 'driver_version': driver_version, 'gpu_model': gpu_model, 'cuda_version': cuda_version,  'cpu_utils': cpu_utils, 'mem_utils': mem_utils, 'cpu_freq': cpu_freq}
    # print(basic_metrics)
    return basic_metrics


def collect_and_insert_data():
    client = connect_influxdb()
    gpu_metrics = {'gpu_status': 0, 'fan_speed': 0, 'temp': 0, 'frequency': 0, 'power': 0}
    gpu_infos = gpu_data()

    max_fan_speed, max_gpu_temp, max_gpu_freq, max_gpu_power = 0, 0, 0, 0
    for gpu in gpu_infos:
        gpu_metrics['gpu_status'] = gpu['gpu_status']
        gpu_metrics['fan_speed'] = int(gpu['fan_speed'].replace(" %", ""))
        if gpu_metrics['fan_speed'] > max_fan_speed:
            max_fan_speed = gpu_metrics['fan_speed']
        gpu_metrics['temp'] = int(re.findall(r"\d+", gpu['temp'])[0])
        if gpu_metrics['temp'] > max_gpu_temp:
            max_gpu_temp = gpu_metrics['temp']
        gpu_metrics['frequency'] = int(re.findall(r"\d+", gpu['frequency'])[0])
        if gpu_metrics['frequency'] > max_gpu_temp:
            max_gpu_freq = gpu_metrics['frequency']
        gpu_metrics['power'] = int(re.findall(r"\d+", gpu['power'])[0])
        if gpu_metrics['power'] > max_gpu_temp:
            max_gpu_power = gpu_metrics['power']

    # 基础数据获取
    basic_metrics = basic_info()

    complete_metrics = {**basic_metrics, **gpu_metrics}

    json_body = [
        {
            "measurement": "hardware",
            "tags": {
                "timestamp": int(time.time()),
                "hostname": socket.gethostname()
            },
            "fields": {
                "host": socket.gethostname(),
                "release": basic_metrics['release'],
                "kernel": basic_metrics['kernel'],
                "driver_version": basic_metrics['driver_version'],
                "cpu_utils": basic_metrics['cpu_utils'],
                "mem_utils": basic_metrics['mem_utils'],
                "cpu_freq": basic_metrics['cpu_freq'],
                "gpu_status": gpu_metrics['gpu_status'],
                "cuda_version": basic_metrics['cuda_version'],
                "gpu_model": basic_metrics['gpu_model'],
                "gpu_fan": max_fan_speed,
                "gpu_temp": max_gpu_temp,
                "gpu_freq": max_gpu_freq,
                "gpu_power": max_gpu_power,

            }
        }
    ]
    insert_influxdb(client, json_body)
    # print(complete_metrics)


def run():

    # 运行30分钟，每5分钟采集一次数据
    # 开始时间
    start_time = time.time()
    end_time = start_time + 1800  #  半小时后结束
    while time.time() < end_time:
        collect_and_insert_data()
        # 等待 5 分钟
        time.sleep(300)


if __name__ == '__main__':
    run()



