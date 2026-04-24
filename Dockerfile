FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY run_dashboard.py ./
COPY config/ ./config/

EXPOSE 8501

CMD ["python", "run_dashboard.py"]
