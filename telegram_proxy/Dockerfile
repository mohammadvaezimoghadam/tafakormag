FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Primary PyPI registry failed. Falling back to devneeds mirror..." && \
     pip install --no-cache-dir -r requirements.txt --index-url https://pypi.devneeds.ir/simple/)

COPY local_proxy.py .

CMD ["python", "local_proxy.py"]
