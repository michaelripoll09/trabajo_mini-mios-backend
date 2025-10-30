"""
Modelos de base de datos para la aplicación de control de gastos
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON
from sqlalchemy.sql import func
try:
    from .database import Base
except ImportError:
    from database import Base
import enum

class TipoTransaccion(str, enum.Enum):
    """Enum para tipos de transacciones"""
    INGRESO = "ingreso"
    GASTO = "gasto"

class Transaccion(Base):
    """
    Modelo para transacciones financieras
    """
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, nullable=False, default=func.now())
    tipo = Column(Enum(TipoTransaccion), nullable=False)
    categoria = Column(String(100), nullable=False)
    monto = Column(Float, nullable=False)
    descripcion = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Transaccion(id={self.id}, tipo={self.tipo}, monto={self.monto})>"

class ArchivoImportado(Base):
    """
    Modelo para almacén libre de filas importadas desde XLS/XLSX
    """
    __tablename__ = 'archivos_importados'
    id = Column(Integer, primary_key=True, index=True)
    datos = Column(JSON, nullable=False)
    fecha_importacion = Column(DateTime, default=func.now())