# Optional Docker-based deploy (Render can also use render.yaml with runtime: python)
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render provides PORT; default fallback for local
ENV PORT=10000
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-t", "60", "-b", "0.0.0.0:${PORT}", "app:app"]
