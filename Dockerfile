# ─────────────────────────────────────────────────────────────
# Dockerfile — Multi-stage build for NoShowIQ
#
# Stage 1 (builder): install dependencies into a clean layer.
# Stage 2 (runtime): copy only what's needed; run as non-root user.
#
# Build:  docker build -t noshow-iq .
# Run:    docker run -p 7860:7860 --env-file .env noshow-iq
# ─────────────────────────────────────────────────────────────

# ── Stage 1: builder ─────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy only the dependency files first so Docker can cache this layer.
# Rebuilds only re-run pip install when requirements.txt changes.
COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ─────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy the application source code
COPY noshow_iq/ ./noshow_iq/
COPY models/    ./models/

# Create a non-root user (security best practice)
RUN addgroup --system appgroup \
 && adduser  --system --ingroup appgroup appuser \
 && chown -R appuser:appgroup /app

USER appuser

# Expose the FastAPI port
EXPOSE 7860

# Healthcheck so Docker/Kubernetes knows if the container is alive
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')"

# Start the API server
CMD ["uvicorn", "noshow_iq.api:app", "--host", "0.0.0.0", "--port", "7860"]
