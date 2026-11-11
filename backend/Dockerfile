FROM python:3.12-slim

# Don't write .pyc files; flush logs immediately (otherwise `docker logs` lags behind).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# GeoDjango needs the GDAL, GEOS and PROJ system libraries.
RUN apt-get update \
    && apt-get install -y --no-install-recommends binutils libproj-dev gdal-bin \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first: this layer is cached and only rebuilt when dependencies change,
# not on every code edit.
ARG REQUIREMENTS=dev
COPY requirements/ requirements/
RUN pip install -r requirements/${REQUIREMENTS}.txt

COPY . .

# Never run the app as root inside the container.
RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
