FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install the package (core deps: django, drf, pyjwt, cryptography)
COPY pyproject.toml README.md ./
COPY drf_keycloak/ ./drf_keycloak/

RUN pip install --upgrade pip && pip install -e .[test]

# Copy test files
COPY tests/ ./tests/
COPY pytest.ini ./
COPY . ./test_project/

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
