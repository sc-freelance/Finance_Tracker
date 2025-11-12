# api/__init__.py
from .expenses import ExpenseAPI
from .forecast import ForecastAPI

__all__ = ['ExpenseAPI', 'ForecastAPI']
# Marks this folder as a Python package and imports API resources
# for easier access when registering routes in the main app.
