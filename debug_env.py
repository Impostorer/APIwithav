import os
from dotenv import load_dotenv

print("🔍 Проверка загрузки .env файла...")

# Получаем текущую директорию
current_dir = os.getcwd()
print(f"📁 Текущая директория: {current_dir}")

# Смотрим что есть в директории
files = os.listdir()
print(f"📋 Файлы в директории: {[f for f in files if f.endswith('.env') or f.endswith('.py')]}")

# Пробуем загрузить .env
load_dotenv()

# Проверяем переменные
print("🔑 Проверка переменных:")
print(f"YC_ACCESS_KEY: {'✅ УСТАНОВЛЕН' if os.getenv('YC_ACCESS_KEY') else '❌ ОТСУТСТВУЕТ'}")
print(f"YC_SECRET_KEY: {'✅ УСТАНОВЛЕН' if os.getenv('YC_SECRET_KEY') else '❌ ОТСУТСТВУЕТ'}")
print(f"YC_BUCKET_NAME: {os.getenv('YC_BUCKET_NAME', '❌ ОТСУТСТВУЕТ')}")

if os.getenv('YC_ACCESS_KEY'):
    print(f"   Начало ACCESS_KEY: {os.getenv('YC_ACCESS_KEY')[:8]}...")
if os.getenv('YC_SECRET_KEY'):
    print(f"   Начало SECRET_KEY: {os.getenv('YC_SECRET_KEY')[:8]}...")