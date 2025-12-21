from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models import City

def increment_city_access(session: Session, city_id: int):
    city = session.query(City).filter(City.id == city_id).first()
    if city:
        city.access_count = (city.access_count or 0) + 1
        city.last_access_at = datetime.utcnow()
        session.commit()
