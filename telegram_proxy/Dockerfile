FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt || \
    (echo "Primary PyPI registry failed. Trying Tsinghua mirror..." && \
     pip install --no-cache-dir --default-timeout=1000 -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn) || \
    (echo "Falling back to devneeds mirror..." && \
     pip install --no-cache-dir --default-timeout=1000 -r requirements.txt --index-url https://pypi.devneeds.ir/simple/ --trusted-host pypi.devneeds.ir)

COPY local_proxy.py .

CMD ["python", "local_proxy.py"]
