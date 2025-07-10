# Dockerfile for the Flask-based traffic visualizer app
FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install flask aiohttp

EXPOSE 5000

CMD ["python", "app.py"]
