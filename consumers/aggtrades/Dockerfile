FROM python:3.11-slim

WORKDIR /app

COPY consumers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY consumers/aggtrades .

ENTRYPOINT ["python", "main.py"]