
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py /app/
ENV PORT=10000
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 app:app
