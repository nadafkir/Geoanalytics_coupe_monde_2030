# eviction/main.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from eviction_service import EvictionService
from db import get_db

def main():
    print("🚀 Service Eviction démarré")

    # Parcourir les sessions de la DB
    for db_session in get_db():
        service = EvictionService(db_session)
        service.run_eviction()

    print("✅ Service Eviction terminé")


if __name__ == "__main__":
    main()
