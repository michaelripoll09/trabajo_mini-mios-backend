"""
Configuración de la base de datos PostgreSQL
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la base de datos (valores por defecto para entorno docker-compose)
def _get_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default

pg_user = _get_env('POSTGRES_USER', 'admin')
pg_password = _get_env('POSTGRES_PASSWORD', 'admin123')
pg_db = _get_env('POSTGRES_DB', 'finanzas_db')
pg_host = _get_env('POSTGRES_HOST', 'db')  # nombre del servicio en docker-compose
pg_port = _get_env('POSTGRES_PORT', '5432')

DATABASE_URL = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

# Crear motor de base de datos
engine = create_engine(DATABASE_URL)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

def get_db():
    """
    Obtener sesión de base de datos
    """
    db = None
    try:
        db = SessionLocal()
        logger.info("Conexión a base de datos establecida")
        yield db
    except Exception as e:
        logger.error(f"Error al conectar con la base de datos: {e}")
        raise
    finally:
        if db:
            db.close()
            logger.info("Conexión a base de datos cerrada")