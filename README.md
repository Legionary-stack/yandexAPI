# Яндекс Диск Клиент

Этот проект позволяет работать с Яндекс Диском через командную строку:
- Загружать файлы и папки
- Скачивать файлы
- Просматривать содержимое диска

## Установка

1. **Клонируйте репозиторий**

   ```bash
   git clone https://github.com/Legionary-stack/yandexAPI.git
   cd ваш_репозиторий
   ```
   
2. **Создайте файл yandexSettings.env в корне проекта и добавьте ваш токен доступа**
    ```env
   YANDEX_ACCESS_TOKEN=y0__...
   YANDEX_BASE_URL=https://cloud-api.yandex.net/v1/disk
   YANDEX_RESOURCES_ENDPOINT=/resources
   YANDEX_UPLOAD_ENDPOINT=/resources/upload
   YANDEX_DOWNLOAD_ENDPOINT=/resources/download
   ```
   
   Чтобы получить токен:
    ```text
    https://yandex.ru/dev/disk/poligon/
    ```
   

## Примеры Использования

```shell
python main.py list "путь/на/диске"

python main.py upload "локальный/файл.txt" "удаленный/путь/"

python main.py upload "локальная/папка" "удаленный/путь/" --type folder

python main.py download "удаленный/файл.txt" "локальный/путь.txt"
```

**Автор**

Банников Максим КН-203
