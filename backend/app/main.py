import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi import FastAPI
from app.routers.pois import router as pois_router
from app.routers.metrics.batch import router as batch_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GeoAnalytics API")
# ⚡ Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou ["http://localhost:3001"] pour plus sûr
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(pois_router)
app.include_router(batch_router)
