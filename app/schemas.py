"""Adaptador para exponer los esquemas desde el módulo raíz `schemas`."""
from importlib import import_module

_schemas = import_module('schemas')

for _name in dir(_schemas):
    if not _name.startswith('_'):
        globals()[_name] = getattr(_schemas, _name)

__all__ = [n for n in globals().keys() if not n.startswith('_')]


