# Stage 1: Build environment
FROM python:3.11-slim-bullseye AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Minimal runtime image
FROM python:3.11-slim-bullseye

# Create a non-root user
RUN groupadd -r aethergroup && useradd -r -g aethergroup aetheruser

WORKDIR /app
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache /wheels/*

COPY packages/ ./packages/
COPY backend/ ./backend/

RUN pip install -e ./packages/aethergrid_core
RUN pip install -e ./packages/models
RUN pip install -e ./packages/theory
RUN pip install -e ./packages/evaluation
RUN pip install -e ./packages/sovereign_watchdog

# Set ownership
RUN chown -R aetheruser:aethergroup /app

# Switch to non-root user
USER aetheruser

# Run server
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
