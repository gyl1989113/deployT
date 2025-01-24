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
from tools.send_alert import send_alert
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
            return [{'gpu_status': 2, 'model': '', 'fan_speed': '0', 'temp': '0', 'frequency': '0', 'power': '0',
                     'cpu_frequency': '0'}]
        # 没有显卡
        if "not found" in error_output:
            return [{'gpu_status': 0, 'model': '', 'fan_speed': '0', 'temp': '0', 'frequency': '0', 'power': '0',
                     'cpu_frequency': '0'}]

    gpu_infos = list()
    xml = ET.XML(result)
    info = parse_xml_to_json(xml)
    for gpu in info.get('gpu'):
        gpu_info = {
            'gpu_status': 1,
            'fan_speed': gpu.get('fan_speed'),
            'temp': gpu.get('temperature')[0].get('gpu_temp'),
            'frequency': gpu.get('clocks')[0].get('graphics'),  # Get the graphics frequency
            'power': gpu.get('gpu_power_readings')[0].get('power_draw'),  # Get the power usage
        }
        print(gpu_info)
        gpu_infos.append(gpu_info)
    return gpu_infos


# 基础指标
def basic_info():
    # cpu使用率
    cpu_util_all = psutil.cpu_percent(interval=1, percpu=True)
    cpu_utils = sum(cpu_util_all)/len(cpu_util_all)
    # 内存使用率
    mem = psutil.virtual_memory()
    mem_utils = (mem.total-mem.free)/mem.total
    # cpu 频率
    cpu_freq = psutil.cpu_freq().current

    basic_metrics = {'cpu_utils': cpu_utils, 'mem_utils': mem_utils, 'cpu_freq': cpu_freq}
    # print(basic_metrics)
    return basic_metrics


def run():
    # client = connect_influxdb()

    gpu_metrics = {'gpu_status': 0, 'fan_speed': 0, 'temp': 0, 'freq': 0, 'power': 0}
    gpu_infos = gpu_data()

    max_fan_speed, max_gpu_temp = 0, 0
    for gpu in gpu_infos:
        gpu_metrics['gpu_status'] = gpu['gpu_status']
        gpu_metrics['model'] = gpu['model']
        gpu_metrics['fan_speed'] = int(gpu['fan_speed'].replace(" %", ""))
        if gpu_metrics['fan_speed'] > max_fan_speed:
            max_fan_speed = gpu_metrics['fan_speed']
        gpu_metrics['temp'] = int(re.findall(r"\d+", gpu['temp'])[0])
        if gpu_metrics['temp'] > max_gpu_temp:
            max_gpu_temp = gpu_metrics['temp']
        gpu_metrics['freq'] = int(re.findall(r"\d+", gpu['freq'])[0])
        if gpu_metrics['freq'] > max_gpu_temp:
            max_gpu_temp = gpu_metrics['freq']
        gpu_metrics['power'] = int(re.findall(r"\d+", gpu['power'])[0])
        if gpu_metrics['power'] > max_gpu_temp:
            max_gpu_temp = gpu_metrics['power']

    # 基础数据获取
    basic_metrics = basic_info()

    complete_metrics = {**basic_metrics, **gpu_metrics}

    # json_body = [
    #     {
    #         "measurement": "hardware",
    #         "tags": {
    #             "timestamp": int(time.time()),
    #             "hostname": socket.gethostname()
    #         },
    #         "fields": {
    #             "host": socket.gethostname(),
    #             "gpu_status": gpu_metrics['gpu_status'],
    #             "gpu_model": gpu_metrics['model'],
    #             "gpu_fan": gpu_metrics['fan_speed'],
    #             "gpu_temp": gpu_metrics['temp'],
    #             "cpu_utils": basic_metrics['cpu_utils'],
    #             "mem_utils": basic_metrics['mem_utils'],
    #             "df_utils_root": basic_metrics['df_utils_root'],
    #             "df_utils_work": basic_metrics['df_utils_work'],
    #             "net_utils": basic_metrics['net_utils'],
    #         }
    #     }
    # ]
    # insert_influxdb(client, json_body)
    print(complete_metrics)


if __name__ == '__main__':
    run()



