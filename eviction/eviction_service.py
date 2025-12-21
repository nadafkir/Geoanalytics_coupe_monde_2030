from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import City, Poi, EvictionAudit

ACCESS_THRESHOLD = 5
DAYS_THRESHOLD = 30  # 30 jours pour la dernière activité

class EvictionService:
    def __init__(self, db: Session):
        self.db = db

    def run_eviction(self):
      if not self._should_run_eviction():
        print(f"[{datetime.utcnow()}] ⏱ Check rapide : moins de {DAYS_THRESHOLD} jours depuis le dernier audit.")
        return

      print(f"[{datetime.utcnow()}] 🚀 Audit Eviction lancé")
      evicted_count = self._evict_cities()
      self._update_last_run()
      print(f"[{datetime.utcnow()}] ✅ Audit Eviction terminé, {evicted_count} villes évictées")
    
    def _should_run_eviction(self) -> bool:
        audit = (
            self.db.query(EvictionAudit)
            .order_by(EvictionAudit.run_at.desc())
            .first()
        )

        if not audit:
            # Premier audit initial
            audit = EvictionAudit(run_at=datetime.utcnow() - timedelta(days=DAYS_THRESHOLD + 1))
            self.db.add(audit)
            self.db.commit()
            print(f"[{datetime.utcnow()}] 🆕 Premier audit initial créé.")
            return True

        days_since_last = (datetime.utcnow() - audit.run_at).days
        print(f"[{datetime.utcnow()}] ⏱ {days_since_last} jours depuis le dernier audit.")
        return days_since_last >= DAYS_THRESHOLD

    def _update_last_run(self, evicted_count: int):
        audit = EvictionAudit(
            run_at=datetime.utcnow(),
            evicted_cities_count=evicted_count,
            status="success",
            message=f"{evicted_count} villes évictées lors de cet audit."
        )
        self.db.add(audit)
        self.db.commit()

    def _evict_cities(self):
      now = datetime.utcnow()
      cities = self.db.query(City).all()
      evicted_count = 0

      for city in cities:
        last_access = city.last_access_at or city.updated_at
        days_inactive = (now - last_access).days if last_access else None

        if city.access_count < ACCESS_THRESHOLD and (days_inactive is None or days_inactive >= DAYS_THRESHOLD):
            self._evict_city(city)
            evicted_count += 1

      self.db.commit()
      return evicted_count
    
    def _evict_city(self, city: City):
        print(f"[{datetime.utcnow()}] 🔥 Eviction de la ville {city.name_fr} (ID {city.id})")
        self.db.query(Poi).filter(Poi.city_id == city.id).delete()
        city.is_evicted = True
        city.pois_count = 0
        self.db.add(city)
