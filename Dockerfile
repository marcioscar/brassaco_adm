# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    locales \
    locales-all \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen pt_BR.UTF-8 \
    && update-locale LANG=pt_BR.UTF-8

# Set locale environment variables
ENV LC_ALL=pt_BR.UTF-8
ENV LANG=pt_BR.UTF-8
ENV LANGUAGE=pt_BR.UTF-8

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install dependencies using pipenv
RUN pipenv install --system --deploy

# Install watchdog for better performance
RUN pip install --no-cache-dir watchdog

# Copy application files
COPY . .

# Create directory for uploaded files
RUN mkdir -p comprovantes

# Copy streamlit config
COPY .streamlit/ ~/.streamlit/

# Expose port
EXPOSE 8507

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8507/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py"]