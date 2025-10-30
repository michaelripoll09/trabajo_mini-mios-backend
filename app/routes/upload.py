"""
Rutas para carga de archivos
"""
import logging
import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, WebSocket
from fastapi import Form
from sqlalchemy.orm import Session
from database import get_db
from ..services.upload_service import UploadService
from ..services import upload_ws
from ..models import ArchivoImportado

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/excel", response_model=dict)
async def cargar_archivo_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Cargar archivo Excel con transacciones
    """
    try:
        # Validar tipo de archivo
        if not file.filename.endswith(('.xls', '.xlsx')):
            raise HTTPException(
                status_code=400, 
                detail="El archivo debe ser de tipo .xls o .xlsx"
            )
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Procesar archivo
            service = UploadService(db)
            resultado = service.procesar_archivo_excel(temp_file_path)
            
            if not resultado.success:
                raise HTTPException(status_code=400, detail=resultado.message)
            
            return resultado.dict()
            
        finally:
            # Limpiar archivo temporal
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint cargar_archivo_excel: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/excel/validate", response_model=dict)
async def validar_archivo_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Validar estructura de archivo Excel antes de cargar
    """
    try:
        # Validar tipo de archivo
        if not file.filename.endswith(('.xls', '.xlsx')):
            raise HTTPException(
                status_code=400, 
                detail="El archivo debe ser de tipo .xls o .xlsx"
            )
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Validar archivo
            service = UploadService(db)
            resultado = service.validar_archivo_excel(temp_file_path)
            
            return resultado.dict()
            
        finally:
            # Limpiar archivo temporal
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint validar_archivo_excel: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/excel/preview", response_model=dict)
async def previsualizar_hojas_excel(
    file: UploadFile = File(...),
    expected_columns: str | None = Form(None),
    db: Session = Depends(get_db)
):
    """
    Listar todas las hojas y columnas para cualquier archivo Excel (no validar columnas por defecto).
    """
    try:
        if not file.filename.endswith((".xls", ".xlsx")):
            raise HTTPException(status_code=400, detail="El archivo debe ser de tipo .xls o .xlsx")

        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            import json
            # Nunca pasar columnas_esperadas si no se reciben
            columnas_esperadas = None
            if expected_columns:
                try:
                    columnas_esperadas = json.loads(expected_columns)
                except Exception:
                    columnas_esperadas = None
            service = UploadService(db)
            resultado = service.listar_y_validar_hojas(temp_file_path, columnas_esperadas)
            return resultado.dict()
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint previsualizar_hojas_excel: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/excel/import-json", response_model=dict)
async def importar_desde_json(
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Importar transacciones desde JSON validado en frontend
    """
    try:
        filas = payload.get('filas', [])
        archivo_nombre = payload.get('archivoNombre')
        lote_id_cli = payload.get('loteId')
        if not isinstance(filas, list) or len(filas) == 0:
            raise HTTPException(status_code=400, detail="Se requiere 'filas' como lista no vacía")

        service = UploadService(db)
        resultado = service.importar_desde_json(filas, archivo_nombre, lote_id_cli)
        return resultado.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint importar_desde_json: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/imported-files", response_model=dict)
def listar_archivos_importados(
    db: Session = Depends(get_db),
    show_hidden: bool = Query(False, description="Si true, incluye registros ocultos")
):
    """
    Devuelve los últimos 100 archivos/fila subidos de cualquier estructura
    """
    try:
        archivos = db.query(ArchivoImportado).order_by(ArchivoImportado.fecha_importacion.desc()).limit(100).all()
        filas_all = [{**a.datos, "id": a.id, "fecha": a.fecha_importacion} for a in archivos]
        filas = [f for f in filas_all if show_hidden or not f.get('oculto')]
        return {"success": True, "filas": filas}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.delete("/imported-files", response_model=dict)
def eliminar_todos_los_importados(db: Session = Depends(get_db)):
    """
    Opción segura: elimina todos los registros importados previamente.
    """
    try:
        db.query(ArchivoImportado).delete()
        db.commit()
        return {"success": True, "message": "Registros importados eliminados"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.post("/imported-files/{lote_id}/hide", response_model=dict)
def ocultar_lote(lote_id: str, db: Session = Depends(get_db)):
    """Marca como oculto todos los registros del lote dado (no elimina)."""
    try:
        archivos = db.query(ArchivoImportado).order_by(ArchivoImportado.id.asc()).all()
        cambios = 0
        for a in archivos:
            d = dict(a.datos or {})
            if d.get('lote_id') == lote_id and not d.get('oculto'):
                d['oculto'] = True
                a.datos = d
                cambios += 1
        if cambios:
            db.commit()
        return {"success": True, "message": f"Lote {lote_id} ocultado", "registros_afectados": cambios}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.post("/imported-files/{lote_id}/restore", response_model=dict)
def restaurar_lote(lote_id: str, db: Session = Depends(get_db)):
    """Quita la marca de oculto a todos los registros del lote dado."""
    try:
        archivos = db.query(ArchivoImportado).order_by(ArchivoImportado.id.asc()).all()
        cambios = 0
        for a in archivos:
            d = dict(a.datos or {})
            if d.get('lote_id') == lote_id and d.get('oculto'):
                d['oculto'] = False
                a.datos = d
                cambios += 1
        if cambios:
            db.commit()
        return {"success": True, "message": f"Lote {lote_id} restaurado", "registros_afectados": cambios}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.websocket("/ws/{lote_id}")
async def ws_upload(websocket: WebSocket, lote_id: str):
    await websocket.accept()
    await upload_ws.register(lote_id, websocket)
    try:
        while True:
            # Mantener viva la conexión
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        upload_ws.unregister(lote_id, websocket)