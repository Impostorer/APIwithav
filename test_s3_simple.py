import boto3
from botocore.client import Config
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=os.getenv('YC_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('YC_SECRET_KEY'),
    region_name='ru-central1',
    config=Config(signature_version='s3v4')
)

try:
    response = s3.list_buckets()
    print("✅ Успех! Доступные бакеты:", [b['Name'] for b in response['Buckets']])
except Exception as e:
    print(f"❌ Ошибка: {e}")