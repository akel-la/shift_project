"""
Сюда импортируем все модели из текущего каталога.
"""

import importlib
from pathlib import Path

_current_dir = Path(__file__).parent

for _module_path in _current_dir.glob("*.py"):
    _module_name = _module_path.stem
    if _module_name == "__init__":
        continue
    importlib.import_module(f".{_module_name}", package=__package__)

# Если будут проблемы при работе цикла -
# можно заменить его на обычные импорты:

# from .user import User
# from .room import Room
# from .slot import Slot
# from .booking import Booking
