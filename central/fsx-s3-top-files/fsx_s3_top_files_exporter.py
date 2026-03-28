#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import time
from threading import Thread, Lock

cache = {"data": "", "timestamp": 0}
cache_lock = Lock()
CACHE_TTL = 300

def get_top_files(directory, limit=10):
    """lfs find --lazy: 부하 없이 초고속 스캔"""
    try:
        # 타임아웃 300초 (5분)
        result = subprocess.run(
            ['lfs', 'find', directory, '--lazy', '--size', '+10G', '--type', 'f'],
            capture_output=True, text=True, timeout=300
        )
        
        files = []
        for filepath in result.stdout.strip().split('\n'):
            if filepath:
                try:
                    stat_result = subprocess.run(
                        ['stat', '-c', '%s', filepath],
                        capture_output=True, text=True, timeout=1
                    )
                    if stat_result.returncode == 0:
                        size = int(stat_result.stdout.strip())
                        relative_path = filepath.replace('/fsx/s3/', '')
                        files.append((size, relative_path))
                except:
                    pass
        
        files.sort(reverse=True)
        return files[:limit]
    except Exception as e:
        print(f"Error in {directory}: {e}")
        return []

def update_cache():
    with cache_lock:
        cache["data"] = '# HELP fsx_s3_top_files_bytes Top 10 files (10GB+)\n# TYPE fsx_s3_top_files_bytes gauge\n'
        cache["timestamp"] = time.time()
    
    while True:
        try:
            metrics = '# HELP fsx_s3_top_files_bytes Top 10 files (10GB+)\n# TYPE fsx_s3_top_files_bytes gauge\n'
            
            for subdir in ['docker', 'public_data', 'project']:
                path = f'/fsx/s3/{subdir}'
                print(f"[{time.strftime('%H:%M:%S')}] Scanning {path}...")
                top_files = get_top_files(path, 10)
                print(f"[{time.strftime('%H:%M:%S')}] Found {len(top_files)} files in {subdir}")
                
                for rank, (size, relative_path) in enumerate(top_files, 1):
                    safe_path = relative_path.replace('"', '').replace('\\', '')[:200]
                    size_gb = size / (1024**3)
                    metrics += f'fsx_s3_top_files_bytes{{directory="{subdir}",rank="{rank}",path="{safe_path}",size_gb="{size_gb:.1f}"}} {size}\n'
                
                with cache_lock:
                    cache["data"] = metrics
                    cache["timestamp"] = time.time()
                print(f"[{time.strftime('%H:%M:%S')}] Updated ({subdir})")
            
            print(f"[{time.strftime('%H:%M:%S')}] ✅ Complete")
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
    server = HTTPServer(('0.0.0.0', 9102), Handler)
    print('FSx Exporter (--lazy, no load) on :9102')
    server.serve_forever()
