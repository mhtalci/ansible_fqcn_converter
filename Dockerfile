FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Install the package
RUN pip install -e .

# Install Ansible collections
RUN ansible-galaxy collection install -r config/collections/requirements.yml

# Create non-root user
RUN useradd -m -u 1000 ansible && \
    chown -R ansible:ansible /app
USER ansible

# Set environment variables
ENV PYTHONPATH=/app
ENV ANSIBLE_HOST_KEY_CHECKING=False

# Default command
CMD ["fqcn-converter", "--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import scripts.convert_to_fqcn; print('OK')" || exit 1

# Labels
LABEL maintainer="mhtalci <hello@mehmetalci.com>"
LABEL description="Ansible FQCN Converter Tool"
LABEL version="1.0.0"