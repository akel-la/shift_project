В pyproject.toml:
```toml
packages = [{include = "app", from = "src"}]
```
Позволяет писать простой импорт:

from app import ...

обращаясь к приложению как к пакету.

src - это просто папка, это не пакет - поэтому в src нет \__init__.py.
app - это пакет, поэтому внутри \__init__.py.
