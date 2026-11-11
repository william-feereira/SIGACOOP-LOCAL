# 1) Telas React
FROM node:22-slim AS telas
WORKDIR /telas
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# 2) Django + Gunicorn
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
# psycopg[binary] já traz a libpq: nenhuma dependência do sistema é necessária.
RUN useradd --system --home /app siga
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=telas /telas/dist /app/frontend/dist
RUN chmod +x /app/docker/entrypoint.sh && mkdir -p /app/private_media /app/staticfiles && chown -R siga /app/private_media /app/staticfiles
USER siga
EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoint.sh"]
