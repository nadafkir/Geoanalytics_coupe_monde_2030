from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Charger variables depuis .env
load_dotenv()

# Déterminer l'hôte automatiquement
is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "true"
DB_HOST = "db" if is_docker else "localhost"

# Construire l'URL
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'password')}@"
    f"{DB_HOST}:{os.getenv('DB_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'geoanalytics')}"
)

print(f"🔗 Connexion à: {SQLALCHEMY_DATABASE_URL.replace(os.getenv('POSTGRES_PASSWORD', ''), '***')}")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
