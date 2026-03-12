from storage_config import storage_config
from file_storage import file_storage

if __name__ == "__main__":
    print("🔍 Проверка подключения к Yandex Cloud S3...")
    
    if storage_config.validate_config():
        try:
            # Пробуем получить список бакетов
            s3_client = storage_config.get_s3_client()
            response = s3_client.list_buckets()
            print("✅ Подключение к Yandex Cloud S3 успешно!")
            print(f"📦 Доступные бакеты: {[bucket['Name'] for bucket in response['Buckets']]}")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
    else:
        print("❌ Конфигурация невалидна")