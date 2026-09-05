FROM python:3.11-slim

WORKDIR /app

# git is needed to clone user-submitted repositories
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/chroma /app/data/repos

EXPOSE 8000

# Shell form (not exec-array form) so ${PORT} is actually substituted --
# Render assigns a dynamic port via the PORT env var and routes traffic
# to it; hardcoding 8000 makes the service unreachable on Render even
# though it starts up fine. Falls back to 8000 for plain `docker run`
# and docker-compose, where PORT usually isn't set.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
