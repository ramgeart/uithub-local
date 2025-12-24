FROM python:3.12-slim

WORKDIR /app

# Install build dependencies if necessary
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the project files
COPY pyproject.toml .
COPY README.md .
COPY src/ ./src/

# Install the package and its dependencies
RUN pip install --no-cache-dir .

# Expose the API port
EXPOSE 8000

# Default command to run the REST API server
CMD ["uithub", "--serve", "--host", "0.0.0.0", "--port", "8000"]
