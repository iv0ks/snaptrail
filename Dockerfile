# Single source of truth for the Python version used by all stages.
ARG PYTHON_VERSION=3.12

######################################################################################################
#############################                  STAGE 1: BUILD                   ######################
######################################################################################################

# Create new stage for building dependencies.
FROM python:${PYTHON_VERSION}-slim AS builder

# Apply available OS security patches before building dependencies.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Set up a working directory for the build context.
WORKDIR /build

# Copy the requirements file into the build context.
COPY requirements.txt .

# Install Python dependencies into a single, version-independent directory.
RUN pip install --no-cache-dir --target=/install -r requirements.txt

######################################################################################################
#############################                  STAGE 2: RUNTIME                 ######################
######################################################################################################

# Create new stage for the runtime environment.
FROM python:${PYTHON_VERSION}-slim AS runtime

# Apply available OS security patches on top of the base image. This picks up fixes (e.g. zlib1g) that are released between base-image updates, keeping the
# scanned runtime image free of fixable OS CVEs. apt lists are removed to keep the image small.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the app.
RUN useradd --create-home --uid 10001 appuser

# Set environment variables for the runtime environment.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/install/bin:${PATH}" \
    PYTHONPATH="/install:/app" \
    DATA_ROOT="/app"

# Set the working directory for the runtime environment.
WORKDIR /app

# Bring in the pre-built dependencies from the builder stage.
COPY --from=builder /install /install

# Copy application code and the served photo gallery.
COPY app ./app
COPY photos ./photos

# Bake the challenge flag INTO the image at build time, at /app/flag.txt —
# OUTSIDE the served photos/ directory on purpose, so path traversal has a target.
# The flag is intentionally NOT committed to the repo (it would spoil the lab).
#
# We create it here (rather than relying on the app's startup seed) because the
# container runs with a read-only root filesystem, so the app cannot write it
# at runtime. When running straight from Python the app seeds it itself; here
# it already exists, so that seed is a no-op. Override with --build-arg FLAG=...
ARG FLAG=FLAG{SNAPTRAIL_OFF_THE_TRAIL}
RUN printf '%s\n' "$FLAG" > /app/flag.txt

# Switch to the non-root user for running the application.
USER appuser

# Expose the port the application will run on.
EXPOSE 5000

# Define a health check to ensure the application is running correctly.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:5000/healthz').read()==b'ok' else sys.exit(1)"

# Serve with gunicorn (production WSGI server) rather than Flask's dev server.
# --worker-tmp-dir /tmp keeps things working under a read-only root filesystem (see docker-compose.yml: read_only + tmpfs /tmp).
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--worker-tmp-dir", "/tmp", "app.main:app"]
