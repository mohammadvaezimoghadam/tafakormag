ARG REGISTRY=""
FROM ${REGISTRY}python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Primary PyPI registry failed/unreachable. Falling back to devneeds mirror..." && \
     pip install --no-cache-dir -r requirements.txt --index-url https://pypi.devneeds.ir/simple/)

COPY . .

RUN mkdir -p /app/logs

CMD ["python", "main.py"]