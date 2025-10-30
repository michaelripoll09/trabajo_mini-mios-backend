"""
Servicio para carga de archivos XLS/XLSX (esquema agnóstico)
"""
import logging
import pandas as pd
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import uuid4
from typing import Optional
from ..models import ArchivoImportado
from ..schemas import RespuestaAPI
from .transaction_service import build_response

logger = logging.getLogger(__name__)

class UploadService:
    """Servicio para manejo de carga de archivos"""
    
    def __init__(self, db: Session):
        self.db = db

    def procesar_archivo_excel(self, file_path: str) -> RespuestaAPI:
        """
        Procesa el Excel y guarda cada fila como JSON en `ArchivoImportado`.
        Sin columnas requeridas ni validaciones de dominio.
        """
        try:
            df = pd.read_excel(file_path)
            df = df.where(pd.notnull(df), None)
            creados = 0
            errores: List[str] = []
            for index, row in df.iterrows():
                try:
                    payload: Dict[str, Any] = {k: row[k] for k in df.columns}
                    self.db.add(ArchivoImportado(datos=payload))
                    creados += 1
                except Exception as e:
                    errores.append(f"Fila {index + 2}: {e}")
            self.db.commit()
            return build_response(
                success=True,
                message=f"Archivo procesado. {creados} filas almacenadas",
                data={"total_filas": int(len(df)), "creados": creados, "errores": errores}
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al procesar archivo Excel: {e}")
            return build_response(success=False, message="Error al procesar archivo Excel", error=str(e))

    def validar_archivo_excel(self, file_path: str) -> RespuestaAPI:
        """
        Exploración no restrictiva: devuelve columnas, tipos inferidos y algunas filas.
        """
        try:
            df = pd.read_excel(file_path, nrows=10)
            columnas_presentes = df.columns.tolist()
            tipos_inferidos = {c: str(df[c].dtype) for c in columnas_presentes}
            return build_response(
                success=True,
                message="Archivo explorado",
                data={
                    "columnas": columnas_presentes,
                    "tipos_inferidos": tipos_inferidos,
                    "filas_ejemplo": int(len(df))
                }
            )
        except Exception as e:
            logger.error(f"Error al explorar archivo Excel: {e}")
            return build_response(success=False, message="Error al explorar archivo", error=str(e))

    def listar_y_validar_hojas(self, file_path: str, columnas_esperadas: List[str] | None = None) -> RespuestaAPI:
        """
        Listar todas las hojas de un Excel y validar su estructura SOLO si se define columnas_esperadas. Si no, no marcar ninguna como inválida.
        """
        try:
            xls = pd.ExcelFile(file_path)
            sheets_info: List[Dict[str, Any]] = []

            for nombre_hoja in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=nombre_hoja)
                columnas_presentes = df.columns.tolist()
                # Si no se requiere validación, ninguna hoja será 'inválida'.
                if not columnas_esperadas or columnas_esperadas == []:
                    faltantes = []
                    valido = True
                else:
                    faltantes = [c for c in columnas_esperadas if c not in columnas_presentes]
                    valido = len(faltantes) == 0
                muestra = df.head(10).to_dict(orient='records')
                sheets_info.append({
                    'nombre': nombre_hoja,
                    'columnas_presentes': columnas_presentes,
                    'faltantes': faltantes,
                    'valido': valido,
                    'total_filas': int(df.shape[0]),
                    'muestra': muestra
                })
            # En este modo siempre mostrar éxito y nunca error por faltantes
            return build_response(
                success=True,
                message="Hojas listadas (sin validación de estructura)",
                data={'sheets': sheets_info, 'columnas_esperadas': columnas_esperadas if columnas_esperadas else []}
            )
        except Exception as e:
            logger.error(f"Error al listar/validar hojas: {e}")
            return build_response(
                success=False,
                message="Error al listar/validar hojas",
                error=str(e)
            )

    async def _emit_progress(self, lote_id: str, processed: int, total: int) -> None:
        try:
            from . import upload_ws
            await upload_ws.send_progress(lote_id, processed, total)
        except Exception:
            pass

    async def _emit_complete(self, lote_id: str) -> None:
        try:
            from . import upload_ws
            await upload_ws.send_complete(lote_id)
        except Exception:
            pass

    def importar_desde_json(self, filas: List[Dict[str, Any]], archivo_nombre: str | None = None, lote_id: Optional[str] = None) -> RespuestaAPI:
        """
        Importa cualquier fila de cualquier estructura de Excel como documento libre JSON (no valida, solo guarda todo).
        """
        try:
            lote_id = lote_id or str(uuid4())
            creados = 0
            total = len(filas)
            for idx, row in enumerate(filas, start=1):
                payload = dict(row or {})
                if archivo_nombre:
                    payload['archivo_nombre'] = archivo_nombre
                payload['lote_id'] = lote_id
                archivo = ArchivoImportado(datos=payload)
                self.db.add(archivo)
                creados += 1
                # Emitir progreso cada 10 elementos o al final
                if idx % 10 == 0 or idx == total:
                    import asyncio
                    asyncio.create_task(self._emit_progress(lote_id, idx, total))
            self.db.commit()
            # Notificar completo
            import asyncio
            asyncio.create_task(self._emit_complete(lote_id))
            return build_response(
                success=True,
                message=f"Importación libre completada. {creados} filas almacenadas (estructura arbitraria)",
                data={"total_creados": creados, "lote_id": lote_id, "archivo_nombre": archivo_nombre}
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al importar datos libres: {e}")
            return build_response(
                success=False,
                message="Error al importar archivos genéricos",
                error=str(e)
            )