"""Wspólna konfiguracja testów: ustawiana przed importem aplikacji."""

import os

# TestClient wysyła nagłówek Host "testserver"; dopuszczamy go wyłącznie w testach.
os.environ.setdefault("AUTODESK_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
