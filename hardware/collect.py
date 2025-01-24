import os
import sys
import re
import time
import socket
import psutil
from xml.etree import ElementTree as ET

local_path = os.getcwd()
o_path = os.path.abspath(os.path.join(local_path, "../../"))  # 返回当前工作目录
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
            'model': gpu.get('product_name'),
            'uuid': gpu.get('uuid'),
            'fan_speed': gpu.get('fan_speed'),
            'temp': gpu.get('temperature')[0].get('gpu_temp'),
            'frequency': gpu.get('clocks').get('graphics'),  # Get the graphics frequency
            'power': gpu.get('power_readings').get('power_draw'),  # Get the power usage
            'cpu_frequency': psutil.cpu_freq().current  # Get the current CPU frequency
        }
        gpu_infos.append(gpu_info)
    print(gpu_infos)
    return gpu_infos


gpu_data()



