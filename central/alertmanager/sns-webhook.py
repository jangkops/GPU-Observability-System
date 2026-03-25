#!/usr/bin/env python3
import json
import boto3
from flask import Flask, request
import os

app = Flask(__name__)

sns_client = boto3.client(
    'sns',
    region_name='us-west-2',
    aws_access_key_id='AKIARSEDSYT4HEQCGDC4',
    aws_secret_access_key='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'
)

TOPIC_ARN = 'arn:aws:sns:us-west-2:107650139384:alertmanager-notifications'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    # Format alert message
    alerts = data.get('alerts', [])
    message_lines = []
    
    for alert in alerts:
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        
        message_lines.append(f"🚨 Alert: {labels.get('alertname', 'Unknown')}")
        message_lines.append(f"Instance: {labels.get('instance', 'Unknown')}")
        message_lines.append(f"Summary: {annotations.get('summary', 'N/A')}")
        message_lines.append(f"Description: {annotations.get('description', 'N/A')}")
        message_lines.append(f"Status: {alert.get('status', 'Unknown')}")
        message_lines.append("-" * 50)
    
    message = "\n".join(message_lines)
    subject = f"[Mogam Alert] {labels.get('alertname', 'Alert')} - {labels.get('instance', 'Unknown')}"
    
    # Send to SNS
    try:
        response = sns_client.publish(
            TopicArn=TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        return {'status': 'success', 'messageId': response['MessageId']}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
