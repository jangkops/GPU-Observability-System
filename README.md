# Mogam Resource Monitoring

모니터링 시스템 전체 구성 파일

## 구조

### central/
중앙 모니터링 서버 (Prometheus + Grafana + Alertmanager)
- **위치**: monitoring 인스턴스 
- **포트**: Prometheus 9090, Grafana 3000 (ALB 80)
- **URL**: http://mogam-grafana-alb-2031646283.us-west-2.elb.amazonaws.com/d/adv2ww5

### exporters/
각 인스턴스의 메트릭 수집기
- **gpu-instances/**: GPU 인스턴스용 (p4d, p4de, g5, head)
  - dcgm-exporter (GPU 메트릭)
  - node-exporter (시스템 메트릭)
  - process-exporter (프로세스 메트릭)
  - gpu_exporter.py (커스텀 GPU 프로세스 추적)

## 배포

### 중앙 서버
```bash
cd central
docker compose up -d
```

### GPU 인스턴스
```bash
cd exporters/gpu-instances
docker compose up -d
```

## 데이터 보존
- Prometheus: 7일 retention
- Grafana: 영구 (볼륨)
- 백업: central/backups/
