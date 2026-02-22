# ALB 및 네트워크 설정

## Application Load Balancer
- **이름**: mogam-grafana-alb
- **DNS**: mogam-grafana-alb-2031646283.us-west-2.elb.amazonaws.com
- **리전**: us-west-2

## Target Group
- **이름**: mogam-grafana-tg
- **ARN**: arn:aws:elasticloadbalancing:us-west-2:107650139384:targetgroup/mogam-grafana-tg/5c9d10b023d593b8
- **프로토콜**: HTTP:80
- **Health Check**: /api/health (200-399)

## 타겟
- Instance: i-08b2e3f1e8dd487ff (monitoring)
- Port: 80
