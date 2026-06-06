"""
Сюда импортируем все классы-модели,
чтобы отсюда импортировать все в alembic:

# env.py:

from app.core.models import *
"""

from app.models.room import *  # noqa
