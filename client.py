from __future__ import annotations

from pathlib import Path
from typing import NamedTuple, Any

import requests
from pydantic_settings import BaseSettings, SettingsConfigDict
from requests.models import Response


class ListFilesResult(NamedTuple):
    """Результат получения списка файлов."""

    response: Response
    files: list[dict[str, Any]] | None


class YandexSettings(BaseSettings):
    """Настройки для Яндекс Диска"""

    access_token: str
    base_url: str
    resources_endpoint: str
    upload_endpoint: str
    download_endpoint: str
    model_config = SettingsConfigDict(env_file="yandexSettings.env", env_prefix='YANDEX_')


class YandexDiskClient:
    """Класс для работы с Яндекс Диском"""

    def __init__(self) -> None:
        self._settings = YandexSettings()  # type: ignore
        self._base_url = self._settings.base_url
        self._headers = {
            "Authorization": f"OAuth {self._settings.access_token}",
            "Accept": "application/json",
        }

    def check_disk_access(self) -> Response:
        """Проверка доступности Диска"""
        return requests.get(self._base_url, headers=self._headers)

    def _ensure_path_exists(self, remote_path: Path | None) -> bool:
        """Рекурсивно создает путь к файлу/папке, если его не существует"""
        if not remote_path:
            return True

        parts = remote_path.parts
        current_path = ""

        for part in parts:
            if not part:
                continue

            current_path = f"{current_path}/{part}" if current_path else part
            if not self._path_exists(Path(current_path)):
                url = f"{self._base_url}{self._settings.resources_endpoint}?path={current_path}"
                response = requests.put(
                    url,
                    headers=self._headers,
                )
                if response.status_code not in (200, 201):
                    raise Exception(
                        f"Ошибка при создании папки {current_path}: {response.status_code} - {response.text}"
                    )

        return True

    def _path_exists(self, path: Path | None) -> bool:
        """Проверяет, существует ли путь на Яндекс Диске"""
        if not path:
            return False

        url = f"{self._base_url}{self._settings.resources_endpoint}?path={path}"
        response = requests.get(url, headers=self._headers)
        return response.status_code == 200

    def upload_file(
            self, local_path: Path | None, remote_path: Path | None, create_new_version: bool = False
    ) -> Response:
        """Загрузка файла на Диск"""
        if create_new_version:
            raise NotImplementedError("Яндекс.Диск не поддерживает версионирование")
        if not local_path:
            raise ValueError("Локальный путь не может быть None")
        if not local_path.exists():
            raise FileNotFoundError(f"Локальный файл не найден: {local_path}")

        url = f"{self._base_url}{self._settings.upload_endpoint}?path={remote_path}&overwrite=true"
        response = requests.get(url, headers=self._headers)

        if response.status_code != 200:
            return response

        upload_url = response.json().get("href")
        if not upload_url:
            raise Exception("Не удалось получить URL для загрузки")

        with open(local_path, 'rb') as f:
            response = requests.put(upload_url, files={"file": f})

        return response

    def upload_folder(self, local_folder: Path | None, remote_folder: Path | None) -> list[Response]:
        """Рекурсивная загрузка папки с содержимым"""

        if not local_folder:
            raise ValueError("Локальная папка не может быть None")
        if not local_folder.is_dir():
            raise NotADirectoryError(f"Локальная папка не найдена: {local_folder}")

        responses = []
        self._ensure_path_exists(remote_folder)

        for item in local_folder.rglob("*"):
            relative_path = item.relative_to(local_folder)
            remote_item_path = Path(remote_folder) / relative_path if remote_folder else relative_path

            if item.is_dir():
                url = f"{self._base_url}{self._settings.resources_endpoint}?path={remote_item_path}"
                response = requests.put(
                    url,
                    headers=self._headers,
                )
                responses.append(response)
            else:
                response = self.upload_file(item, remote_item_path)
                responses.append(response)

        return responses

    def download_file(self, remote_path: Path | None, local_path: Path | None) -> Response:
        """Скачивание файла с Диска с полной обработкой ошибок"""
        try:
            if not remote_path:
                raise ValueError("Не указан путь к файлу на Яндекс Диске")

            url = f"{self._base_url}{self._settings.download_endpoint}?path={remote_path}"
            response = requests.get(
                url,
                headers=self._headers,
            )

            if response.status_code != 200:
                error_msg = response.json().get("message", "Ошибка")
                raise Exception(f"Яндекс.Диск вернул ошибку: {error_msg} (код {response.status_code})")

            download_url = response.json().get("href")
            if not download_url:
                raise Exception("Не удалось получить URL для скачивания")

            file_response = requests.get(download_url, stream=True)
            if file_response.status_code != 200:
                raise Exception(f"Ошибка при загрузке файла: {file_response.status_code}")

            download_path = Path(local_path) if local_path else Path(remote_path.name)
            if download_path.parent:
                download_path.parent.mkdir(parents=True, exist_ok=True)

            with download_path.open("wb") as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"Файл успешно скачан: {remote_path} -> {download_path}")
            return file_response

        except Exception as e:
            print(f"Ошибка при скачивании файла: {str(e)}")
            raise

    def list_files(self, remote_path: Path | None = None) -> ListFilesResult:
        """Получение списка файлов на Диске"""
        try:
            path_to_list = str(remote_path) if remote_path else ""
            url = f"{self._base_url}{self._settings.resources_endpoint}?path={path_to_list}&limit=1000"
            response = requests.get(
                url,
                headers=self._headers,
            )

            if response.status_code != 200:
                return ListFilesResult(response=response, files=None)

            items = response.json().get("_embedded", {}).get("items", [])
            return ListFilesResult(response=response, files=items)
        except Exception as e:
            print(f"Ошибка при получении списка файлов: {str(e)}")
            raise