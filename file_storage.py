import uuid
import os
from typing import Optional
from fastapi import UploadFile, HTTPException
from storage_config import storage_config

class FileStorageService:
    def __init__(self):
        self.s3_client = storage_config.get_s3_client()
        self.bucket_name = storage_config.bucket_name
    
    async def upload_file(self, file: UploadFile) -> str:
        """Загружает файл в Yandex Cloud S3 и возвращает URL (оригинальный метод)"""
        try:
            # Генерируем уникальное имя файла
            file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Читаем содержимое файла
            file_content = await file.read()
            
            # Загружаем в S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=file_content,
                ContentType=file.content_type
            )
            
            # Генерируем публичный URL (если бакет публичный)
            file_url = f"https://{self.bucket_name}.storage.yandexcloud.net/{unique_filename}"
            
            return file_url
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Ошибка загрузки файла: {str(e)}"
            )
    
    async def upload_file_bytes(self, file_bytes: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
        try:
            print(f"🔼 Начинаем загрузку файла в S3...")
            print(f"📁 Имя файла: {filename}")
            print(f"📏 Размер файла: {len(file_bytes)} bytes")
            print(f"📄 Content-Type: {content_type}")
            print(f"📦 Бакет: {self.bucket_name}")
        
            # Проверяем доступность S3 клиента
            print("🔧 Проверяем S3 клиент...")
            print(f"   Access Key: {storage_config.access_key[:10]}...")  # Первые 10 символов
            print(f"   Bucket: {self.bucket_name}")
            print(f"   Endpoint: {storage_config.endpoint_url}")

            # Генерируем уникальное имя файла
            file_extension = os.path.splitext(filename)[1] if filename else ""
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            print(f"🔤 Уникальное имя файла: {unique_filename}")
        
            # Пробуем загрузить в S3
            print("🔼 Загружаем файл в S3...")
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=file_bytes,
                ContentType=content_type
            )
            print("✅ Файл успешно загружен в S3")
        
            # Генерируем публичный URL
            file_url = f"https://{self.bucket_name}.storage.yandexcloud.net/{unique_filename}"
            print(f"🌐 Сгенерирован URL: {file_url}")
        
            return file_url
        
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при загрузке файла: {str(e)}")
            print(f"🔧 Тип ошибки: {type(e).__name__}")
            import traceback
            print(f"📋 Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500, 
                detail=f"Ошибка загрузки файла: {str(e)}"
            )
    
    async def delete_file(self, file_url: str) -> bool:
        """Удаляет файл из Yandex Cloud S3"""
        try:
            # Извлекаем имя файла из URL
            filename = file_url.split("/")[-1]
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            return True
            
        except Exception as e:
            print(f"Ошибка удаления файла: {str(e)}")
            return False
    
    def get_file_url(self, filename: str) -> str:
        """Генерирует URL для файла"""
        return f"https://{self.bucket_name}.storage.yandexcloud.net/{filename}"

# Глобальный экземпляр сервиса
file_storage = FileStorageService()