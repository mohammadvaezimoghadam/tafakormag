ARG REGISTRY=""
FROM ${REGISTRY}python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -i https://pypi.tuna.tsinghua.edu.cn/simple/ -r requirements.txt || \
    pip install --no-cache-dir --default-timeout=100 -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt || \
    pip install --no-cache-dir --default-timeout=100 -r requirements.txt

COPY . .

RUN mkdir -p /app/logs

CMD ["python", "main.py"]
