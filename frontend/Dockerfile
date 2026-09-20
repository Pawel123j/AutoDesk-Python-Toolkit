# syntax=docker/dockerfile:1

# ── Etap budowania ──────────────────────────────────────────────────────
FROM node:20-slim AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# Adres backendu wchodzi do bundla w czasie budowania — Vite podmienia
# `import.meta.env.*` na stałe, więc nie da się go zmienić po zbudowaniu.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# ── Etap serwowania ─────────────────────────────────────────────────────
# Osobny obraz, żeby do wyniku nie trafił ani node_modules, ani kod
# źródłowy — sam zbudowany katalog dist.
FROM nginx:alpine AS serve

COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
