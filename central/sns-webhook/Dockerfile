FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir boto3 flask requests

COPY webhook.py .

EXPOSE 5001

CMD ["python", "webhook.py"]
