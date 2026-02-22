#!/usr/bin/env python3
import subprocess
import time
from prometheus_client import start_http_server, Gauge

gpu_process_memory = Gauge('gpu_process_memory_mib', 'GPU memory used by process', ['gpu', 'pid', 'username', 'process', 'status'])

def get_gpu_utilization(gpu_idx):
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=index,utilization.gpu', '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5)
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) == 2 and parts[0] == str(gpu_idx):
                    return float(parts[1])
    except:
        pass
    return 0.0

def get_process_runtime(pid):
    try:
        with open('/proc/{}/stat'.format(pid), 'r') as f:
            stat = f.read().split()
            starttime = int(stat[21])
            with open('/proc/uptime', 'r') as uptime_file:
                uptime = float(uptime_file.read().split()[0])
            hz = 100
            runtime = uptime - (starttime / hz)
            return runtime
    except:
        return 0

def determine_status(gpu_idx, pid, memory_mib):
    util = get_gpu_utilization(gpu_idx)
    runtime = get_process_runtime(pid)
    if util < 1.0:
        if runtime > 3600:
            return 'idle_long'
        else:
            return 'loading'
    elif util < 30:
        return 'idle'
    else:
        return 'active'

def get_gpu_processes():
    try:
        result = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_bus_id,pid,used_memory', '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5)
        processes = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) == 3:
                    processes.append({'bus_id': parts[0], 'pid': parts[1], 'memory': parts[2]})
        return processes
    except:
        return []

def get_gpu_index(bus_id):
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=gpu_bus_id,index', '--format=csv,noheader'], capture_output=True, text=True, timeout=5)
        for line in result.stdout.strip().split('\n'):
            if bus_id in line:
                return line.split(',')[1].strip()
    except:
        pass
    return '0'

def get_username(pid):
    try:
        with open('/proc/{}/status'.format(pid), 'r') as f:
            for line in f:
                if line.startswith('Uid:'):
                    uid = line.split()[1]
                    try:
                        with open('/etc/passwd', 'r') as passwd:
                            for pline in passwd:
                                parts = pline.split(':')
                                if parts[2] == uid:
                                    return parts[0]
                    except:
                        pass
                    return uid
    except:
        pass
    return 'unknown'

def get_process_name(pid):
    try:
        with open('/proc/{}/comm'.format(pid), 'r') as f:
            return f.read().strip()
    except:
        return 'unknown'

if __name__ == '__main__':
    start_http_server(9500)
    print('GPU Process Exporter started on :9500')
    while True:
        gpu_process_memory._metrics.clear()
        processes = get_gpu_processes()
        for proc in processes:
            gpu_idx = get_gpu_index(proc['bus_id'])
            username = get_username(proc['pid'])
            process_name = get_process_name(proc['pid'])
            status = determine_status(gpu_idx, proc['pid'], float(proc['memory']))
            gpu_process_memory.labels(gpu=gpu_idx, pid=proc['pid'], username=username, process=process_name, status=status).set(float(proc['memory']))
        time.sleep(15)
