"""
Esquemas Pydantic para validación de datos
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
try:
    from .models import TipoTransaccion
except ImportError:
    from models import TipoTransaccion

class TransaccionBase(BaseModel):
    """Esquema base para transacciones"""
    fecha: datetime
    tipo: TipoTransaccion
    categoria: str = Field(..., max_length=100)
    monto: float = Field(..., gt=0)
    descripcion: Optional[str] = Field(None, max_length=500)

class TransaccionCreate(TransaccionBase):
    """Esquema para crear transacciones"""
    pass

class TransaccionUpdate(BaseModel):
    """Esquema para actualizar transacciones"""
    fecha: Optional[datetime] = None
    tipo: Optional[TipoTransaccion] = None
    categoria: Optional[str] = Field(None, max_length=100)
    monto: Optional[float] = Field(None, gt=0)
    descripcion: Optional[str] = Field(None, max_length=500)

class TransaccionResponse(TransaccionBase):
    """Esquema para respuesta de transacciones"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ResumenFinanciero(BaseModel):
    """Esquema para resumen financiero"""
    total_ingresos: float
    total_gastos: float
    balance: float
    gastos_por_categoria: dict
    ingresos_mensuales: dict
    gastos_mensuales: dict

class RespuestaAPI(BaseModel):
    """Esquema para respuestas uniformes de la API"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None