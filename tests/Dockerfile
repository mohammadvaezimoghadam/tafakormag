FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install project backend dependencies first to leverage Docker build cache
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Primary PyPI registry unreachable. Falling back to devneeds mirror..." && \
     pip install --no-cache-dir -r requirements.txt --index-url https://pypi.devneeds.ir/simple/)

# Install test framework dependencies
RUN pip install --no-cache-dir pytest pytest-django pytest-playwright responses httpx tzdata || \
    (echo "Primary PyPI registry unreachable. Falling back to devneeds mirror for test packages..." && \
     pip install --no-cache-dir pytest pytest-django pytest-playwright responses httpx tzdata --index-url https://pypi.devneeds.ir/simple/)

# Playwright browsers are already pre-installed in this image. 
# We just verify and install system dependencies if needed, or ensure they are present.
RUN playwright install-deps chromium

# The code will be mounted as a volume during development and test runs
