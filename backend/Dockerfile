ARG REGISTRY=""
FROM ${REGISTRY}python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Primary PyPI registry failed/unreachable. Falling back to devneeds mirror..." && \
     pip install --no-cache-dir -r requirements.txt --index-url https://pypi.devneeds.ir/simple/)

COPY backend/ .

RUN python manage.py collectstatic --noinput

COPY backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]