# Use official lightweight Python 3.11 image
FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy pyproject.toml first for better layer caching
COPY pyproject.toml /app/

# Install Python dependencies using uv
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY . /app/

# Create non-root user and give ownership
RUN useradd -m appuser && chown -R appuser:appuser /app

USER appuser

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Default command to run the Streamlit app (replace app.py with your entrypoint if different)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]