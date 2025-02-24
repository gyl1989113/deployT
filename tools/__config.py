# -*- coding: utf-8 -*-
"""配置文件"""


"MySQL 线上配置"
# MySQL 地址(str)
MYSQL_HOST = "127.0.0.1"
# MySQL 端口(int)
MYSQL_PORT = 3306
# MySQL 数据库(str)
MYSQL_DATABASE = "mysql"
# # MySQL 表名(str)
MYSQL_TABLE = "sys_users"
# MySQL 用户名
MYSQL_USER = "root"
# MySQL 密码
MYSQL_PASSWORD = "6block666"

"Redis 线上配置"
# Redis 地址(str)
REDIS_HOST = "127.0.0.1"
# Redis 端口(int)
REDIS_PORT = 6379
# Redis 密码
REDIS_PASSWORD = "pool57836"

"influxdb 线上配置"
# influxdb 地址(str)
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