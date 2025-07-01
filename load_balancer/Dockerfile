FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY load_balancer.py .

EXPOSE 5000

CMD ["uvicorn", "load_balancer:app", "--host", "0.0.0.0", "--port", "5000"]
