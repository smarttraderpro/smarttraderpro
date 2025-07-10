# Dockerfile for Smart Trader Hub Backend

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/app" # Add /app to PYTHONPATH

# Set work directory to /app (project root inside container)
WORKDIR /app

# Install system dependencies (if any)
# RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements file from backend directory on host to /app/backend/requirements.txt in container
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the entire backend directory from host to /app/backend in container
COPY ./backend /app/backend

# Copy alembic.ini from host project root to /app/alembic.ini in container
COPY alembic.ini /app/alembic.ini

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# Uvicorn will be run from /app WORKDIR.
# The application `main:app` is located at `backend/app/main.py`.
# So, the path to the app object is `backend.app.main:app`.
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
