"""
Servicio para operaciones de transacciones
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..models import Transaccion, TipoTransaccion
from ..schemas import TransaccionCreate, TransaccionUpdate, RespuestaAPI, TransaccionResponse

logger = logging.getLogger(__name__)

def build_response(success: bool, message: str, data: Any = None, error: str = None) -> RespuestaAPI:
    """
    Construir respuesta uniforme para la API
    """
    return RespuestaAPI(
        success=success,
        message=message,
        data=data,
        error=error
    )

class TransactionService:
    """Servicio para manejo de transacciones"""
    
    def __init__(self, db: Session):
        self.db = db

    def crear_transaccion(self, transaccion: TransaccionCreate) -> RespuestaAPI:
        """
        Crear una nueva transaccion
        """
        try:
            db_transaccion = Transaccion(**transaccion.dict())
            self.db.add(db_transaccion)
            self.db.commit()
            self.db.refresh(db_transaccion)
            
            logger.info(f"Transacción creada exitosamente: ID {db_transaccion.id}")
            return build_response(
                success=True,
                message="Transacción creada exitosamente",
                data={"id": db_transaccion.id}
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear transacción: {e}")
            return build_response(
                success=False,
                message="Error al crear transacción",
                error=str(e)
            )

    def obtener_transacciones(self, skip: int = 0, limit: int = 100) -> RespuestaAPI:
        """
        Obtener lista de transacciones con paginación
        """
        try:
            transacciones = self.db.query(Transaccion).offset(skip).limit(limit).all()
            total = self.db.query(Transaccion).count()
            # Serializar a esquemas Pydantic (evitar objetos SQLAlchemy en la respuesta)
            transacciones_serializadas = [
                TransaccionResponse.model_validate(t).model_dump()
                for t in transacciones
            ]
            
            logger.info(f"Transacciones obtenidas: {len(transacciones)} de {total}")
            return build_response(
                success=True,
                message="Transacciones obtenidas exitosamente",
                data={
                    "transacciones": transacciones_serializadas,
                    "total": total,
                    "skip": skip,
                    "limit": limit
                }
            )
        except Exception as e:
            logger.error(f"Error al obtener transacciones: {e}")
            return build_response(
                success=False,
                message="Error al obtener transacciones",
                error=str(e)
            )

    def obtener_transaccion_por_id(self, transaccion_id: int) -> RespuestaAPI:
        """
        Obtener transacción por ID
        """
        try:
            transaccion = self.db.query(Transaccion).filter(Transaccion.id == transaccion_id).first()
            
            if not transaccion:
                logger.warning(f"Transacción no encontrada: ID {transaccion_id}")
                return build_response(
                    success=False,
                    message="Transacción no encontrada",
                    error="Transacción no existe"
                )
            
            logger.info(f"Transacción obtenida: ID {transaccion_id}")
            return build_response(
                success=True,
                message="Transacción obtenida exitosamente",
                data=TransaccionResponse.model_validate(transaccion).model_dump()
            )
        except Exception as e:
            logger.error(f"Error al obtener transacción {transaccion_id}: {e}")
            return build_response(
                success=False,
                message="Error al obtener transacción",
                error=str(e)
            )

    def actualizar_transaccion(self, transaccion_id: int, transaccion_update: TransaccionUpdate) -> RespuestaAPI:
        """
        Actualizar transacción existente
        """
        try:
            db_transaccion = self.db.query(Transaccion).filter(Transaccion.id == transaccion_id).first()
            
            if not db_transaccion:
                logger.warning(f"Transacción no encontrada para actualizar: ID {transaccion_id}")
                return build_response(
                    success=False,
                    message="Transacción no encontrada",
                    error="Transacción no existe"
                )
            
            # Actualizar campos
            update_data = transaccion_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_transaccion, field, value)
            
            self.db.commit()
            self.db.refresh(db_transaccion)
            
            logger.info(f"Transacción actualizada: ID {transaccion_id}")
            return build_response(
                success=True,
                message="Transacción actualizada exitosamente",
                data=TransaccionResponse.model_validate(db_transaccion).model_dump()
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al actualizar transacción {transaccion_id}: {e}")
            return build_response(
                success=False,
                message="Error al actualizar transacción",
                error=str(e)
            )

    def eliminar_transaccion(self, transaccion_id: int) -> RespuestaAPI:
        """
        Eliminar transacción
        """
        try:
            db_transaccion = self.db.query(Transaccion).filter(Transaccion.id == transaccion_id).first()
            
            if not db_transaccion:
                logger.warning(f"Transacción no encontrada para eliminar: ID {transaccion_id}")
                return build_response(
                    success=False,
                    message="Transacción no encontrada",
                    error="Transacción no existe"
                )
            
            self.db.delete(db_transaccion)
            self.db.commit()
            
            logger.info(f"Transacción eliminada: ID {transaccion_id}")
            return build_response(
                success=True,
                message="Transacción eliminada exitosamente"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al eliminar transacción {transaccion_id}: {e}")
            return build_response(
                success=False,
                message="Error al eliminar transacción",
                error=str(e)
            )

    def obtener_resumen_financiero(self) -> RespuestaAPI:
        """
        Obtener resumen financiero para dashboard
        """
        try:
            # Total de ingresos
            total_ingresos = self.db.query(func.sum(Transaccion.monto)).filter(
                Transaccion.tipo == TipoTransaccion.INGRESO
            ).scalar() or 0
            
            # Total de gastos
            total_gastos = self.db.query(func.sum(Transaccion.monto)).filter(
                Transaccion.tipo == TipoTransaccion.GASTO
            ).scalar() or 0
            
            # Balance
            balance = total_ingresos - total_gastos
            
            # Gastos por categoría
            gastos_por_categoria = self.db.query(
                Transaccion.categoria,
                func.sum(Transaccion.monto).label('total')
            ).filter(
                Transaccion.tipo == TipoTransaccion.GASTO
            ).group_by(Transaccion.categoria).all()
            
            gastos_categoria_dict = {cat: float(total) for cat, total in gastos_por_categoria}
            
            # Ingresos mensuales (últimos 12 meses)
            ingresos_mensuales = self.db.query(
                extract('year', Transaccion.fecha).label('año'),
                extract('month', Transaccion.fecha).label('mes'),
                func.sum(Transaccion.monto).label('total')
            ).filter(
                Transaccion.tipo == TipoTransaccion.INGRESO,
                Transaccion.fecha >= datetime.now() - timedelta(days=365)
            ).group_by(
                extract('year', Transaccion.fecha),
                extract('month', Transaccion.fecha)
            ).all()
            
            ingresos_mensuales_dict = {
                f"{int(año)}-{int(mes):02d}": float(total) 
                for año, mes, total in ingresos_mensuales
            }
            
            # Gastos mensuales (últimos 12 meses)
            gastos_mensuales = self.db.query(
                extract('year', Transaccion.fecha).label('año'),
                extract('month', Transaccion.fecha).label('mes'),
                func.sum(Transaccion.monto).label('total')
            ).filter(
                Transaccion.tipo == TipoTransaccion.GASTO,
                Transaccion.fecha >= datetime.now() - timedelta(days=365)
            ).group_by(
                extract('year', Transaccion.fecha),
                extract('month', Transaccion.fecha)
            ).all()
            
            gastos_mensuales_dict = {
                f"{int(año)}-{int(mes):02d}": float(total) 
                for año, mes, total in gastos_mensuales
            }
            
            resumen = {
                "total_ingresos": float(total_ingresos),
                "total_gastos": float(total_gastos),
                "balance": float(balance),
                "gastos_por_categoria": gastos_categoria_dict,
                "ingresos_mensuales": ingresos_mensuales_dict,
                "gastos_mensuales": gastos_mensuales_dict
            }
            
            logger.info("Resumen financiero generado exitosamente")
            return build_response(
                success=True,
                message="Resumen financiero obtenido exitosamente",
                data=resumen
            )
        except Exception as e:
            logger.error(f"Error al generar resumen financiero: {e}")
            return build_response(
                success=False,
                message="Error al generar resumen financiero",
                error=str(e)
            )