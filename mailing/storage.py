# -*- coding: utf-8 -*-
"""Хранение рассылок в JSON-файле.

Данные не теряются между запусками программы: при старте рассылки
загружаются из файла, после каждого изменения — записываются обратно.
Файл открывается через контекстный менеджер ``with``, поэтому он
гарантированно закрывается даже при ошибке.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .exceptions import StorageError, ValidationError
from .models import Mailing


class JsonStorage:
    """Чтение и запись рассылок в JSON-файл."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """Путь к файлу данных."""
        return self._path

    def load(self) -> list[Mailing]:
        """Загрузить рассылки из файла.

        Если файла ещё нет, возвращается пустой список — это нормальная
        ситуация при первом запуске программы.
        """
        if not self._path.exists():
            return []
        try:
            with self._path.open(encoding="utf-8") as file:
                raw_data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise StorageError(
                f"не удалось прочитать файл данных {self._path}"
            ) from error
        if not isinstance(raw_data, list):
            raise StorageError(f"неверный формат файла данных {self._path}")
        try:
            return [Mailing.from_dict(item) for item in raw_data]
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            raise StorageError(f"повреждённые данные в файле {self._path}") from error

    def save(self, mailings: Iterable[Mailing]) -> None:
        """Записать рассылки в файл (файл перезаписывается целиком)."""
        data = [mailing.to_dict() for mailing in mailings]
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.write("\n")
        except OSError as error:
            raise StorageError(
                f"не удалось сохранить данные в файл {self._path}"
            ) from error

    def __repr__(self) -> str:
        return f"JsonStorage(path={str(self._path)!r})"
