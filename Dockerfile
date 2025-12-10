FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear carpeta de media (montable como volumen)
RUN mkdir -p /app/media

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn ginebra_app.wsgi:application --bind 0.0.0.0:8000"]
