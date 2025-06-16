FROM python:3.11.8-slim-bookworm
WORKDIR /app

# Update system packages to reduce vulnerabilities
RUN apt-get update && apt-get dist-upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]