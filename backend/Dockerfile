# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Nie kompiluj .pyc i nie buforuj stdout — w kontenerze logi mają
# pojawiać się od razu, a pliki .pyc tylko puchną warstwę.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Zależności osobną warstwą: zmiana kodu nie unieważnia cache'u instalacji.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

# Katalog na generowane pliki (XLSX, raporty). Musi istnieć zanim
# aplikacja spróbuje do niego zapisać.
RUN mkdir -p /app/generated

# Uruchomienie bez roota. Kontener, który przetwarza pliki wrzucane
# przez użytkownika, nie ma powodu działać z pełnymi uprawnieniami.
RUN useradd --create-home --uid 10001 toolkit && chown -R toolkit:toolkit /app
USER toolkit

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/', timeout=2).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
