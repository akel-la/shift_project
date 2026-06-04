from sqlalchemy.orm import DeclarativeBase


# Класс, от которого наследуются все другие классы-таблицы.
# Сюда помещать все поля, которые должны быть общими для всех таблиц:
class Base(DeclarativeBase):
    pass
