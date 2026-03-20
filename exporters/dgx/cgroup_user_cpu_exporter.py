#!/usr/bin/env python3
"""Cgroup-based user CPU exporter - compatible with namedprocess_namegroup metrics"""
import time
from prometheus_client import start_http_server, Counter
from pathlib import Path

# Use Counter (not Gauge) so rate() works correctly in Prometheus
user_cpu = Counter('namedprocess_namegroup_cpu_seconds_total', 'CPU seconds by user (cgroup)', ['username', 'groupname', 'mode', 'instance', 'instance_type'])

INSTANCE = 'dgx'
INSTANCE_TYPE = 'dgx-a100'

def get_username(uid):
    try:
        for line in open('/etc/passwd'):
            parts = line.split(':')
            if parts[2] == uid:
                return parts[0]
    except:
        pass
    return uid

def get_cgroup_cpu():
    result = {}
    cgroup_base = Path('/sys/fs/cgroup/user.slice')
    if not cgroup_base.exists():
        return result
    for d in cgroup_base.iterdir():
        if not d.name.startswith('user-'):
            continue
        uid = d.name.split('-')[1].split('.')[0]
        cpu_stat = d / 'cpu.stat'
        if not cpu_stat.exists():
            continue
        try:
            user_usec = 0
            system_usec = 0
            for line in cpu_stat.read_text().splitlines():
                if line.startswith('user_usec'):
                    user_usec = int(line.split()[1])
                elif line.startswith('system_usec'):
                    system_usec = int(line.split()[1])
            username = get_username(uid)
            result[username] = {'user': user_usec / 1_000_000, 'system': system_usec / 1_000_000}
        except:
            pass
    return result

# Track previous values to increment counter correctly
prev_values = {}

def collect():
    global prev_values
    current = get_cgroup_cpu()
    for username, vals in current.items():
        for mode in ['user', 'system']:
            key = (username, mode)
            cur_val = vals[mode]
            prev_val = prev_values.get(key, cur_val)
            delta = cur_val - prev_val
            if delta > 0:
                user_cpu.labels(
                    username=username,
                    groupname=f'cgroup;{username}',
                    mode=mode,
                    instance=INSTANCE,
                    instance_type=INSTANCE_TYPE
                ).inc(delta)
            prev_values[key] = cur_val

if __name__ == '__main__':
    start_http_server(9256)
    print('Cgroup User CPU Exporter started on :9256 (namedprocess compatible)')
    while True:
        collect()
        time.sleep(15)
