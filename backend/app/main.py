import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi import FastAPI
from app.routers.pois import router as pois_router
from app.routers.metrics.batch import router as batch_router

app = FastAPI(title="GeoAnalytics API")

app.include_router(pois_router)
app.include_router(batch_router)
