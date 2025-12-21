import logging
from logging.handlers import RotatingFileHandler
import os

# Dossier des logs dans le conteneur
log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)  # Crée le dossier si nécessaire

log_file = os.path.join(log_dir, "backend.log")

# Logger principal
logger = logging.getLogger("backend_logger")
logger.setLevel(logging.INFO)

# Handler fichier avec rotation
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.info(f"Log file path inside container: {log_file}")
