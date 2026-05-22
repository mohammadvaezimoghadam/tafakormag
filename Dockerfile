ARG REGISTRY=""
FROM ${REGISTRY}python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Primary PyPI registry failed/unreachable. Falling back to devneeds mirror..." && \
     pip install --no-cache-dir -r requirements.txt --index-url https://pypi.devneeds.ir/simple/)

COPY . .

RUN python manage.py collectstatic --noinput

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]