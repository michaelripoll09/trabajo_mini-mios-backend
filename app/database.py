"""Adaptador para importar la configuración de base de datos del módulo raíz.

Permite que las importaciones `from app.database ...` funcionen sin mover
el archivo `database.py` que vive en la raíz del proyecto.
"""
from importlib import import_module

_db = import_module('database')

engine = _db.engine
Base = _db.Base
SessionLocal = _db.SessionLocal
get_db = _db.get_db


