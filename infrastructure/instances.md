# 모니터링 대상 인스턴스

## GPU 인스턴스

### p4de (p4de.24xlarge)
- IP: 10.0.1.196
- GPU: 8x A100 80GB
- Exporters: 9100 (node), 9400 (dcgm), 9256 (process), 9500 (gpu-custom)

### p4d (p4d.24xlarge)
- IP: 10.0.1.26
- GPU: 8x A100 40GB
- Exporters: 9100, 9400, 9256, 9500

### g5 (g5.12xlarge)
- IP: 10.0.1.101
- GPU: 4x A10G
- Exporters: 9100, 9400, 9256, 9500

### head (g4dn.xlarge)
- IP: 10.0.1.195
- GPU: 1x T4
- Exporters: 9100, 9400, 9256

### p5 (p5.48xlarge)
- IP: 10.0.2.94
- GPU: 8x H100
- Exporters: 9100, 9400, 9256, 9500

## CPU 인스턴스

### r7 (r7i.4xlarge)
- IP: 10.0.1.50
- Exporters: 9100 (node), 9256 (process)

## 중앙 모니터링

### monitoring
- Instance: i-08b2e3f1e8dd487ff
- Services: Prometheus (9090), Grafana (80), Alertmanager (9093), FSx Exporter (9101)
