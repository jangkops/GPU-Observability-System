#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import os

class FSxExporter(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            try:
                # 전체 사용량
                result = subprocess.run(['lfs', 'df', '/fsx'], capture_output=True, text=True, timeout=5)
                total = used = 0
                for line in result.stdout.split('\n'):
                    if 'OST' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            total += int(parts[1]) * 1024
                            used += int(parts[2]) * 1024
                
                metrics = f'''# HELP fsx_lustre_bytes FSx Lustre filesystem bytes
# TYPE fsx_lustre_bytes gauge
fsx_lustre_bytes{{type="total"}} {total}
fsx_lustre_bytes{{type="used"}} {used}
fsx_lustre_bytes{{type="available"}} {total - used}

# HELP fsx_user_quota_bytes FSx user quota usage in bytes (전체 FSx)
# TYPE fsx_user_quota_bytes gauge
'''
                
                # 사용자별 quota (전체 FSx - 기존 유지)
                if os.path.exists('/fsx/home'):
                    for username in os.listdir('/fsx/home'):
                        quota_result = subprocess.run(
                            ['lfs', 'quota', '-u', username, '/fsx'],
                            capture_output=True, text=True, timeout=2
                        )
                        if quota_result.returncode == 0:
                            for line in quota_result.stdout.split('\n'):
                                if '/fsx' in line and 'Filesystem' not in line:
                                    parts = line.split()
                                    if len(parts) >= 2 and parts[1].isdigit():
                                        bytes_used = int(parts[1]) * 1024
                                        metrics += f'fsx_user_quota_bytes{{username="{username}"}} {bytes_used}\n'
                                    break
                
                # /fsx/s3 하위 디렉토리별 사용량 (프로젝트 quota)
                metrics += '\n# HELP fsx_s3_directory_bytes FSx /fsx/s3 directory usage in bytes\n'
                metrics += '# TYPE fsx_s3_directory_bytes gauge\n'
                
                projects = {'docker': 1001, 'project': 1002, 'public_data': 1003}
                for dirname, proj_id in projects.items():
                    quota_result = subprocess.run(
                        ['lfs', 'quota', '-p', str(proj_id), '/fsx'],
                        capture_output=True, text=True, timeout=2
                    )
                    if quota_result.returncode == 0:
                        for line in quota_result.stdout.split('\n'):
                            if '/fsx' in line and 'Filesystem' not in line:
                                parts = line.split()
                                if len(parts) >= 2 and parts[1].isdigit():
                                    bytes_used = int(parts[1]) * 1024
                                    metrics += f'fsx_s3_directory_bytes{{directory="{dirname}"}} {bytes_used}\n'
                                break
                
                # /fsx/home 사용자별 사용량 (프로젝트 quota 3001~3023) - 신규 추가
                metrics += '\n# HELP fsx_home_user_bytes FSx /fsx/home user directory usage in bytes\n'
                metrics += '# TYPE fsx_home_user_bytes gauge\n'
                
                home_users = {
                    'cgjang': 3001, 'aychoi': 3002, 'bskim': 3003, 'ckkang': 3004,
                    'enhuh': 3005, 'hblee': 3006, 'hermee': 3007, 'hjshin': 3008,
                    'hklee': 3009, 'hslee': 3010, 'intern': 3011, 'jwlee': 3012,
                    'jykim2': 3013, 'sbkim': 3014, 'shlee': 3015, 'shlee2': 3016,
                    'sjchoe': 3017, 'srpark': 3018, 'syseo': 3019, 'ybkim': 3020,
                    'yjgo': 3021, 'ymbaek': 3022, 'yokim': 3023
                }
                for username, proj_id in home_users.items():
                    quota_result = subprocess.run(
                        ['lfs', 'quota', '-p', str(proj_id), '/fsx'],
                        capture_output=True, text=True, timeout=2
                    )
                    if quota_result.returncode == 0:
                        for line in quota_result.stdout.split('\n'):
                            if '/fsx' in line and 'Filesystem' not in line:
                                parts = line.split()
                                if len(parts) >= 2 and parts[1].isdigit():
                                    bytes_used = int(parts[1]) * 1024
                                    metrics += f'fsx_home_user_bytes{{user="{username}"}} {bytes_used}\n'
                                break
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(metrics.encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 9101), FSxExporter)
    print('FSx Exporter running on :9101')
    server.serve_forever()
