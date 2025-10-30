"""
Rutas para manejo de transacciones
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from ..schemas import TransaccionCreate, TransaccionUpdate, TransaccionResponse
from ..services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/", response_model=dict)
async def crear_transaccion(
    transaccion: TransaccionCreate,
    db: Session = Depends(get_db)
):
    """
    Crear una nueva transacción
    """
    try:
        service = TransactionService(db)
        resultado = service.crear_transaccion(transaccion)
        
        if not resultado.success:
            raise HTTPException(status_code=400, detail=resultado.message)
        
        return resultado.dict()
    except Exception as e:
        logger.error(f"Error en endpoint crear_transaccion: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/", response_model=dict)
async def obtener_transacciones(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a retornar"),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de transacciones con paginación
    """
    try:
        service = TransactionService(db)
        resultado = service.obtener_transacciones(skip=skip, limit=limit)
        
        if not resultado.success:
            raise HTTPException(status_code=400, detail=resultado.message)
        
        return resultado.dict()
    except Exception as e:
        logger.error(f"Error en endpoint obtener_transacciones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/{transaccion_id}", response_model=dict)
async def obtener_transaccion_por_id(
    transaccion_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener transacción por ID
    """
    try:
        service = TransactionService(db)
        resultado = service.obtener_transaccion_por_id(transaccion_id)
        
        if not resultado.success:
            if "no encontrada" in resultado.message.lower():
                raise HTTPException(status_code=404, detail=resultado.message)
            raise HTTPException(status_code=400, detail=resultado.message)
        
        return resultado.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint obtener_transaccion_por_id: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/{transaccion_id}", response_model=dict)
async def actualizar_transaccion(
    transaccion_id: int,
    transaccion_update: TransaccionUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar transacción existente
    """
    try:
        service = TransactionService(db)
        resultado = service.actualizar_transaccion(transaccion_id, transaccion_update)
        
        if not resultado.success:
            if "no encontrada" in resultado.message.lower():
                raise HTTPException(status_code=404, detail=resultado.message)
            raise HTTPException(status_code=400, detail=resultado.message)
        
        return resultado.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint actualizar_transaccion: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.delete("/{transaccion_id}", response_model=dict)
async def eliminar_transaccion(
    transaccion_id: int,
    db: Session = Depends(get_db)
):
    """
    Eliminar transacción
    """
    try:
        service = TransactionService(db)
        resultado = service.eliminar_transaccion(transaccion_id)
        
        if not resultado.success:
            if "no encontrada" in resultado.message.lower():
                raise HTTPException(status_code=404, detail=resultado.message)
            raise HTTPException(status_code=400, detail=resultado.message)
        
        return resultado.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint eliminar_transaccion: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")