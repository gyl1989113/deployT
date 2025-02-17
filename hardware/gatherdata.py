import platform
import os
import re
import subprocess
import json
import socket
import time

import psutil
from xml.etree import ElementTree as ET

# 显卡型号映射表

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


def parse_xml_to_json(xml):
    response = {}
    for child in list(xml):
        # flag = False
        # for filter in filter_list:
        #     if filter in child.tag:
        #         flag = True
        #         break
        # if not flag:
        #     continue
        if len(list(child)) > 0:
            if not response.get(child.tag):
                response[child.tag] = []
            response[child.tag].append(parse_xml_to_json(child))
        elif child.text.strip() != 'N/A' and child.text.strip() != '':
            response[child.tag] = child.text.strip()

    return response


def get_basic_info():
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

    print(basic_info)
    return basic_info


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


def get_variable_info():
    # cpu 频率
    cpu_freq = psutil.cpu_freq().current
    cpu_freq = "{:.2f}".format(cpu_freq)

    # gpu 相关
    gpu_metrics = {'gpu_status': 0, 'fan_speed': 0, 'temp': 0, 'frequency': 0, 'power': 0}
    gpu_infos = gpu_data()

    # 只保留gpu最大值
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

    variable_info = {'cpu_freq': cpu_freq, 'gpu_status': gpu_metrics['gpu_status'], 'gpu_fan': max_fan_speed, 'gpu_temp': max_gpu_temp, 'gpu_freq': max_gpu_freq, 'gpu_power': max_gpu_power}
    print(variable_info)
    return variable_info


def run_gather_variable_data():
    variable_data = []
    # 运行30分钟，每5分钟采集一次数据
    # 开始时间
    start_time = time.time()
    end_time = start_time + 1800  # 半小时后结束
    while time.time() < end_time:
        variable_data.append(get_variable_info())
        # 等待 5 分钟
        time.sleep(60)

    # 保存数据
    return variable_data


if __name__ == '__main__':
    basic_info = get_basic_info()
    variable_data = run_gather_variable_data()
    print("最后的收集数据是：")
    print(variable_data)

