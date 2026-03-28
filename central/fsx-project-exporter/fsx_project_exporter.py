#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import time
from threading import Thread, Lock
import os

cache = {"data": "", "timestamp": 0}
cache_lock = Lock()
CACHE_TTL = 21600  # 6시간

def get_directory_size(directory):
    """lfs find --lazy로 파일 목록, stat으로 크기 계산"""
    try:
        result = subprocess.run(
            ['lfs', 'find', directory, '--lazy', '-type', 'f'],
            capture_output=True, text=True, timeout=60
        )
        
        total = 0
        count = 0
        for filepath in result.stdout.strip().split('\n'):
            if filepath and count < 1000:
                count += 1
                try:
                    stat_result = subprocess.run(
                        ['stat', '-c', '%s', filepath],
                        capture_output=True, text=True, timeout=1
                    )
                    if stat_result.returncode == 0:
                        total += int(stat_result.stdout.strip())
                except:
                    pass
        
        return total
    except:
        return 0

def update_cache():
    with cache_lock:
        cache["data"] = '# HELP fsx_project_directory_bytes Project directory sizes\n# TYPE fsx_project_directory_bytes gauge\n'
        cache["timestamp"] = time.time()
    
    while True:
        try:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting scan...")
            metrics = '# HELP fsx_project_directory_bytes Project directory sizes\n# TYPE fsx_project_directory_bytes gauge\n'
            
            dirs = []
            for item in os.listdir('/fsx/s3/project'):
                path = f'/fsx/s3/project/{item}'
                if os.path.isdir(path):
                    dirs.append((item, path))
            
            dirs.sort()
            for idx, (name, path) in enumerate(dirs, 1):
                print(f"[{time.strftime('%H:%M:%S')}] Scanning {name} ({idx}/{len(dirs)})...")
                size = get_directory_size(path)
                size_gb = size / (1024**3)
                safe_name = name.replace('"', '').replace('\\', '')
                metrics += f'fsx_project_directory_bytes{{directory="{safe_name}",size_gb="{size_gb:.1f}"}} {size}\n'
            
            with cache_lock:
                cache["data"] = metrics
                cache["timestamp"] = time.time()
            
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scan complete. Next scan in 6 hours.")
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(CACHE_TTL)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            with cache_lock:
                if cache["data"]:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(cache["data"].encode())
                else:
                    self.send_response(503)
                    self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    Thread(target=update_cache, daemon=True).start()
    time.sleep(1)
    server = HTTPServer(('0.0.0.0', 9103), Handler)
    print('FSx Project Directory Exporter (6h interval) on :9103')
    server.serve_forever()
