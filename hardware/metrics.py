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
    # Parse the XML data
    info = ET.fromstring(result)
    for gpu in info.find('gpu'):
        gpu_info = {
            'gpu_status': 1,
            'fan_speed': gpu.find('fan_speed').text,
            'temp': gpu.find('temperature/gpu_temp').text,
            'frequency': gpu.find('clocks/graphics_clock').text,  # Get the graphics frequency
            'power': gpu.find('gpu_power_readings/power_draw').text,  # Get the power usage
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


gpu_data()



