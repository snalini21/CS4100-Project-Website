FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends fluidsynth libfluidsynth-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
