"""
Rutas para análisis financiero
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from ..services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/resumen", response_model=dict)
async def obtener_resumen_financiero(
    db: Session = Depends(get_db)
):
    """
    Obtener resumen financiero para dashboard
    """
    try:
        service = TransactionService(db)
        resultado = service.obtener_resumen_financiero()
        
        if not resultado.success:
            raise HTTPException(status_code=400, detail=resultado.message)
        
        return resultado.dict()
    except Exception as e:
        logger.error(f"Error en endpoint obtener_resumen_financiero: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/gastos-por-categoria", response_model=dict)
async def obtener_gastos_por_categoria(
    db: Session = Depends(get_db)
):
    """
    Obtener gastos agrupados por categoría
    """
    try:
        service = TransactionService(db)
        resultado = service.obtener_resumen_financiero()
        
        if not resultado.success:
            raise HTTPException(status_code=400, detail=resultado.message)
        
        # Extraer solo los gastos por categoría
        gastos_por_categoria = resultado.data.get("gastos_por_categoria", {})
        
        return {
            "success": True,
            "message": "Gastos por categoría obtenidos exitosamente",
            "data": gastos_por_categoria
        }
    except Exception as e:
        logger.error(f"Error en endpoint obtener_gastos_por_categoria: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/tendencias-mensuales", response_model=dict)
async def obtener_tendencias_mensuales(
    db: Session = Depends(get_db)
):
    """
    Obtener tendencias de ingresos y gastos mensuales
    """
    try:
        service = TransactionService(db)
        resultado = service.obtener_resumen_financiero()
        
        if not resultado.success:
            raise HTTPException(status_code=400, detail=resultado.message)
        
        # Extraer datos mensuales
        ingresos_mensuales = resultado.data.get("ingresos_mensuales", {})
        gastos_mensuales = resultado.data.get("gastos_mensuales", {})
        
        return {
            "success": True,
            "message": "Tendencias mensuales obtenidas exitosamente",
            "data": {
                "ingresos_mensuales": ingresos_mensuales,
                "gastos_mensuales": gastos_mensuales
            }
        }
    except Exception as e:
        logger.error(f"Error en endpoint obtener_tendencias_mensuales: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")