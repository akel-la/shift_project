#! /usr/bin/env python3
"""
Скрипт генерации секретного ключа.
Полученный ключ запишите в переменную SECRET_KEY в файл .env.
"""

import secrets


def generate_secret_key(length: int = 64) -> str:
    """
    Генерирует случайную строку из 16-ричных цифр.
    """
    return secrets.token_hex(length)


if __name__ == "__main__":
    key = generate_secret_key()
    print("\nСгенерирован новый SECRET_KEY.")
    print("\nДобавьте эту строку в ваш .env файл:\n")
    print(f"SECRET_KEY={key}")
