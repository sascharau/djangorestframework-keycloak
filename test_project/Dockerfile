FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install the package
COPY pyproject.toml README.rst ./
COPY drf_keycloak/ ./drf_keycloak/

RUN pip install --upgrade pip && pip install -e .[dev] && pip install PyJWT cryptography

# Copy test files
COPY tests/ ./tests/
COPY pytest.ini ./
COPY . ./test_project/

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
