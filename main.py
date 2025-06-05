import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

from client import YandexDiskClient


def get_client() -> YandexDiskClient:
    """Возвращает клиент для Яндекс Диска"""
    return YandexDiskClient()


def print_file_list(items: List[Dict[str, Any]]) -> None:
    """Выводит список файлов в удобном формате"""
    for item in items:
        item_type = "папка" if item.get("type") == "dir" else "файл"
        print(f"{item_type:<5} {item.get('name')}" f" ({item.get('size', 'N/A')} bytes)")


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Парсер аргументов с поддержкой пробелов в путях"""
    parser = argparse.ArgumentParser(description="Yandex Disk CLI Client")

    subparsers = parser.add_subparsers(dest="command", required=True)

    upload_parser = subparsers.add_parser("upload", help="Загрузить файл или папку")
    upload_parser.add_argument(
        "source",
        help="Путь к локальному файлу или папке (можно в кавычках)",
    )
    upload_parser.add_argument(
        "destination",
        help="Удаленный путь в облачном хранилище (можно в кавычках)",
    )
    upload_parser.add_argument(
        "--type",
        choices=["file", "folder"],
        help="Укажите тип загружаемого объекта",
    )

    download_parser = subparsers.add_parser("download", help="Скачать файл из облака")
    download_parser.add_argument(
        "source",
        help="Удаленный путь к файлу в облаке (можно в кавычках)",
    )
    download_parser.add_argument(
        "destination",
        help="Локальный путь для сохранения файла (можно в кавычках)",
    )

    list_parser = subparsers.add_parser("list", help="Список файлов в облаке")
    list_parser.add_argument(
        "path",
        nargs="?",
        default="",
        help="Путь в облачном хранилище (можно в кавычках)",
    )

    return parser.parse_args(args)


def main() -> None:
    try:
        args = parse_args()
        client = get_client()
        access_response = client.check_disk_access()

        if access_response.status_code != 200:
            print(f"Ошибка доступа к Яндекс Диску: {access_response.status_code}")
            print(access_response.text)
            return

        if args.command == "upload":
            source = Path(args.source).expanduser().resolve()
            destination = Path(args.destination.strip("\"'"))

            if not source.exists():
                raise FileNotFoundError(f"Локальный путь не существует: {source}")

            upload_type = args.type.lower() if args.type else "folder" if source.is_dir() else "file"

            if upload_type == "folder":
                print(f"Загрузка папки '{source}' в '{destination}'...")
                responses = client.upload_folder(source, destination)
                print(f"Успешно загружено {len(responses)} элементов")
            else:
                print(f"Загрузка файла '{source}' в '{destination}'...")
                response = client.upload_file(source, destination)
                if response.status_code in (200, 201):
                    print("Файл успешно загружен!")
                else:
                    print(f"Ошибка загрузки: {response.status_code}")
                    print(response.text)

        elif args.command == "download":
            source = Path(args.source.strip("\"'"))
            destination = Path(args.destination).expanduser().resolve()

            print(f"Скачивание '{source}' в '{destination}'...")

            destination.parent.mkdir(parents=True, exist_ok=True)

            response = client.download_file(source, destination)
            if response.status_code == 200:
                print("Файл успешно скачан!")
            else:
                print(f"Ошибка скачивания: {response.status_code}")
                print(response.text)

        elif args.command == "list":
            path = Path(args.path.strip("\"'")) if args.path else Path("/")
            print(f"Содержимое '{path}' на Яндекс Диске:")

            result = client.list_files(path)
            if result.response.status_code != 200:
                print(f"Ошибка получения списка файлов: {result.response.status_code}")
                print(result.response.text)
            elif not result.files:
                print("Папка пуста")
            else:
                print_file_list(result.files)

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        if hasattr(e, "response") and hasattr(e.response, "text"):
            print("Детали ошибки:", e.response.text)


if __name__ == "__main__":
    main()