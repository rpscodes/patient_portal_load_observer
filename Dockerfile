# Dockerfile for the Flask-based traffic visualizer app
FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install "flask[async]==2.3.3" aiohttp==3.9.3

EXPOSE 5000

CMD ["python", "app.py"]
