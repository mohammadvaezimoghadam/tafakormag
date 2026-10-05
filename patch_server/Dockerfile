ARG REGISTRY=""
FROM ${REGISTRY}python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY server.py .

RUN mkdir -p /app/patches /app/data

EXPOSE 8080

CMD ["python", "server.py"]
