import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

# Import des routes de ton projet
from app.routers.pois import router as pois_router
from app.routers.metrics.batch import router as batch_router

# Prometheus
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# =========================
# INITIALISATION FASTAPI
# =========================
app = FastAPI(title="DIMA MAGHRIB GeoAnalytics API")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou ["http://localhost:3001"] pour plus de sécurité
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(pois_router)
app.include_router(batch_router)

# =========================
# METRICS PROMETHEUS
# =========================
# Compteur de requêtes HTTP
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint"]
)

# Histogramme du temps de réponse
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"]
)

# Middleware pour collecter les métriques
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(
        request.method,
        request.url.path
    ).inc()

    REQUEST_LATENCY.labels(
        request.method,
        request.url.path
    ).observe(duration)

    return response

# Endpoint /metrics pour Prometheus
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
