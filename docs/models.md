# ИМЕНА:

Таблицы БД в snake_case - нижний регистр, разделение слов (room_slots), множественное число.

Классы моделей в стиле python, т.е. в PascalCase - единственное число, с слова с большой буквы, без нижнего подчеркивания.

# FOREIGN KEY И RELATIONSHIP:

## Foreign key - связь на уровне БД.

1. У всех - ondelete="CASCADE", т.е. при удалении записи из главной таблицы, автоматически удаляются соответствующие записи из подчиненных.
Не может быть бронирований или слотов на несуществующую комнату.

(+) Согласованность данных на уровне БД - надежно, все в одном месте.

(+) Более простой код delete запросов.

(+) Любой delete - это один запрос в БД, а не 2 и более.

## Relationship - связь на уровне языка Python, работа с SQLAlchemy.

(+) Позволяет обращаться к записям из связанных таблиц через объект.атрибут, пример:
room.slots

(+) Проще сохранять связанные данные.

(+) При асинхронном сеансе обращение к незагруженному атрибуту (room.slots) вызовет ошибку, поэтому связанные объекты нужно загружать явно (например, selectinload).
Это защищает от случайных синхронных вызовов.

(+) cascade="all, delete-orphan" - управляет жизненным циклом объектов в сессии.
passive_deletes=True - SQLAlchemy не пытаться загружать дочерние объекты при удалении родителя, если БД сама делает CASCADE (повышает производительность).

# РЕШЕНИЕ ПРОБЛЕМЫ ЦИКЛИЧЕСКИХ / ПРЕЖДЕВРЕМЕННЫХ ИМПОРТОВ:

Если 2 связанные таблицы в разных файлах, то тогда:

1. В аннотациях используем имена классов в виде строк: Не Child, а "Child".

2. Пишем конструкцию:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .other_modult import OtherClass

class SomeClass(Base):
    ...
```

РЕШЕНИЕ:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .booking import Booking
```

Так же рекомендуется использовать в аннотациях строки, а не имена классов, пример:

Использовать:
```python
class Room:
    ...
    slots: Mapped[list["Slot"]] = relationship
```

Вместо:
```python
class Room:
    ...
    slots: Mapped[list[Slot]] = relationship
```


(+) Защищает от проблемы циклических импортов, когда таблица А имеет relationship / ForeignKey на таблицу В, а таблица В имеет relationship / ForeignKey на таблицу А.

(+) Ускорение загрузки - не подгружаются лишние объекты.

(+) Сохранили аннотации для IDE и линтеров.

# КАТЕГОРИАЛЬНОЕ ПОЛЕ:

Есть много разных подходов, остановились на:

```python
import enum

class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    ADMIN = "admin"
```
В БД хранится как обычная строка.

(+) Универсальность - обычные строки есть в любой БД любой версии.
(+) Удобство работы на уровне python - легко читается, IDE, линтеры, изменения и прочее.
(-) Внимательно делать запросы напрямую в БД, минуя приложение - добавление записи со значением не из UserRole, запрос будет выполнен, но на уровне приложения будет не корректная работа бизнес логики.
(-) Могут быть проблемы при добавлении новых ролей (к примеру, модератор) - нужно будет посмотреть код alembic миграций, но добавление новых ролей происходит очень редко.
Так же добавлено значение по умолчанию на уровне БД.

# ПРОВЕРКИ И ОГРАНИЧЕНИЯ:

Добавили те проверки / ограничения, которые можно реализовать средствами БД, не используя слишком сложную логику (пример сложной логики - проверить, что все временные слоты не перекрываются с новым слотом).

Если есть проверки, которые можно выполнить не используя данные из БД - добавляем их на уровень БД (надежность, БД - конечная точка) и дублируем на уровне Pydantic схем - чтобы раньше отсекать не корректные запросы и уменьшить количество запросов к БД.

# ИНДЕКСЫ:

На тех полях, по которым будет идти поиск.

Тип индекса:
У PostgreSQL - это B-Tree, он используется для всего, как универсальное решение (для простых проектов - подойдет).
У SQLite - это так же B-Tree.

Если поле имеет:
foreingkey
primarykey
unique

то СУБД автоматически создает для этого поля индекс, поэтому прописывать index=True не нужно (в одних библиотеках и их версиях это никак не будет влиять не результат, в других приведет к ошибкам).

# ИМПОРТЫ И ALEMBIC:

Все таблицы наследуются от class Base(DeclarativeBase), который находится в app.core.base (все, что в единственном экземпляре на весь проект - лежит в core).
Все таблицы импортируются в файл \__init__.py в каталоге modules, откуда идет импорт в alembic.env:

```python
from app.core.base import Base  # noqa
from app.models import *  # noqa
```

В \__init__.py есть сложный код:

```python
from pathlib import Path
import importlib

_current_dir = Path(__file__).parent

for _module_path in _current_dir.glob("*.py"):
    _module_name = _module_path.stem
    if _module_name == "__init__":
        continue
    importlib.import_module(f".{_module_name}", package=__package__)
```

, который в цикле проходится по всем файлам из modules, кроме \__init__.py,  импортирует все классы-таблицы из всех файлов.
Таким образом, при добавлении/удалении/изменении файлов и таблиц в них - не нужно каждый раз менять импорты в других файлах.

Чтобы точно работало - импортируем сам пакет:

```python
import app.models
```

# ПРОЧЕЕ:

## RELATIONSHIP И FOREIGN KEY (ПОДРОБНО ПРО СИНТАКСИС):

### СИНТАКСИС:

```python
class Base(DeclarativeBase):
    pass


class Parent(Base):
    __tablename__ = "parents"

    ...

    # Здесь:
    # children - имя атрибута, через которое обращаться к объектам из связанной таблицы.
    # Связан со многими объектами из другой таблицы - поэтому в аннотации list["Child"], а не "Child". В аннотации указывается имя связанного класса.
    # back_populates - это то, как будет называться атрибут объектов связанной таблицы.
    # One-to-many:
    # back_populates - единственное число (One).
    # имя атрибута - множественное число (Many).
    children: Mapped[[list["Child"]]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )

class Child(Base):
    __tablename__ = "childrens"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    parent_id: Mapped[int] = mapped_colunm(ForeignKey("parents.id"))
    # Many-to-One:
    # back_populates - множественное число (Many).
    # имя атрибута - единственное число (One).
    parent: Mapped[Optional["Parent"]] = relationship(
        back_populates="children",
    )
```

### ДЛЯ ЧЕГО НУЖНЫ:

relationship - это инструмент на уровне ORM:

1. Позволяет обращаться к объектам из связанных таблиц через объект.атрибут:

child.parent
parent.child

2. Управляет загрузкой связанных данных:

По умолчанию:

```python
parent = session.get(Parent, 1)  # SELECT parent ...
print(parent.children)           # SELECT children ...
```
Параметр в relationship может переопределять это поведение.

3. Каскадные операции на уровне сессии - определяется, какие действия над родителем автоматически применяются к дочерним объектам в сессии.

4. Граф объектов:

parent.child[2].child_from_the_child

ForeignKey - это тот же ForeignKey, что и на уровне СУБД. Relationship без ForeignKey (почти) никогда работать не будет.
Почти всегда если есть ForeignKey, то есть и Relationship.

### CASCADE В RELATIONSHIP:

Параметр cascade определяет, какие операции над родительским объектом каскадируются на дочерние объекты в рамках сессии.
Значения CASCADE:

1. save-update (по умолчанию) - при session.add(parent), происходи session.add(children).
2. delete - при session.delete(parent), удаляет и детей.
3. delete-orphan - если дочерний объект убран из коллекции родителя, то он так же будет удален при flush.
... прочие варианты.
4. all - использовать поведение всех предоставленных вариантов.

Часто используемая комбинация:
... = relationship(
...,
cascade = "all, delete-orphan", - дети не живут без родителя.
passive_deletes = True - не генерировать отдельные DELETE SQL запросы для детей при удалении родителя, расчет на то, что эту работу выполнит CASCADE на уровне СУБД.
)

### КАТЕГОРИАЛЬНОЕ ПОЛЕ - ПРИНИМАЕТ ОДНО ИЗ ФИКСИРОВАННОГО НАБОРА ЗНАЧЕНИЙ:

(1) Python enum.Enum:

```python
class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    role: Mapped[UserRole] = mapped_column(
        default=UserRole.EMPLOYEE,
        server_default=UserRole.EMPLOYEE.value,
        nullable=False,
        )
```

(+) Понятно, наглядно на уровне ORM.
(-) Нет защиты на СУБД уровне - т.е. прямой SQL запрос, не через приложение, не знает о ограничениях.

(2) CHECK проверка на уровне СУБД:

```python
class Booking(Base):
    __tablename__ = "bookings"

    ...
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'cancelled')",
            name="ck_bookings_status"
        ),
    )
```

(+) Зашита на СУБД уровне.

(3) SQLAlchemy Enum + native_enum=False (VARCHAR + CHECK):

(+) Защита на СУБД уровне.

(4) PostgreSQL Enum:

(+) Защита на СУБД уровне.
(-) Работает только для PostgreSQL.

(5) Связанная таблица ролей на уровне СУБД:
