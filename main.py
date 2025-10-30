"""
Aplicación principal FastAPI para Control de Gastos
"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base
from sqlalchemy import text
from app.routes import transactions, analytics, upload

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación
    """
    # Startup
    try:
        # Crear tablas de base de datos
        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar base de datos: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Aplicación cerrada correctamente")

# Crear aplicación FastAPI
app = FastAPI(
    title="Control de Gastos API",
    description="API para gestión de transacciones financieras",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://frontend:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")

@app.get("/")
async def root():
    """
    Endpoint raíz
    """
    return {
        "message": "Control de Gastos API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Verificar conexión a base de datos
        from database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)