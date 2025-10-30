"""Adaptador para exponer los modelos desde el módulo raíz `models`."""
from importlib import import_module

_models = import_module('models')

for _name in dir(_models):
    if not _name.startswith('_'):
        globals()[_name] = getattr(_models, _name)

__all__ = [n for n in globals().keys() if not n.startswith('_')]


