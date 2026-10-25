FROM node:22-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

RUN pip install --no-cache-dir uv

COPY backend/pyproject.toml ./pyproject.toml
RUN uv sync --no-dev --no-install-project

COPY backend ./
COPY --from=frontend-build /app/frontend/out ./static

EXPOSE 8000

CMD ["uv", "run", "--no-project", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
