import os
import boto3
from botocore.client import Config
from dotenv import load_dotenv

# ЯВНО загружаем .env файл ПЕРВЫМ делом
load_dotenv()

print("🔄 Инициализация Yandex Storage Config...")

class YandexStorageConfig:
    def __init__(self):
        # Получаем переменные напрямую из os.getenv()
        self.access_key = os.getenv("YC_ACCESS_KEY")
        self.secret_key = os.getenv("YC_SECRET_KEY")
        self.bucket_name = os.getenv("YC_BUCKET_NAME", "school-platform-files")
        self.endpoint_url = "https://storage.yandexcloud.net"
        self.region = "ru-central1"
        
        print(f"🔧 S3 Config:")
        print(f"   Access Key: {self.access_key[:8] + '...' if self.access_key else '❌ NOT SET'}")
        print(f"   Secret Key: {self.secret_key[:8] + '...' if self.secret_key else '❌ NOT SET'}")
        print(f"   Bucket: {self.bucket_name}")
        print(f"   Endpoint: {self.endpoint_url}")
    
    def get_s3_client(self):
        """Создает и возвращает S3 клиент для Yandex Cloud"""
        if not self.access_key:
            raise Exception("❌ YC_ACCESS_KEY не установлен!")
        if not self.secret_key:
            raise Exception("❌ YC_SECRET_KEY не установлен!")
            
        print("🔑 Создаем S3 клиент с полученными ключами...")
        
        try:
            session = boto3.session.Session()
            client = session.client(
                service_name='s3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(signature_version='s3v4')
            )
            print("✅ S3 клиент успешно создан")
            return client
        except Exception as e:
            print(f"❌ Ошибка создания S3 клиента: {e}")
            raise
    
    def validate_config(self):
        """Проверяет корректность конфигурации"""
        if not all([self.access_key, self.secret_key, self.bucket_name]):
            print("❌ Отсутствуют обязательные переменные для Yandex Cloud S3")
            return False
        print("✅ Конфигурация Yandex Cloud S3 корректна")
        return True

# Глобальный экземпляр конфигурации
storage_config = YandexStorageConfig()