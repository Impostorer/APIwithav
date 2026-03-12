import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Тестируем подключение к PostgreSQL...")

connection_params = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'practiceHub'),
    'user': os.getenv('DB_USER', 'student'),
    'password': os.getenv('DB_PASSWORD', '12345')
}

print(f"📊 Параметры подключения:")
for key, value in connection_params.items():
    if key == 'password':
        print(f"  {key}: {'*' * len(value)}")
    else:
        print(f"  {key}: {value}")

try:
    conn = psycopg2.connect(**connection_params)
    print("✅ Подключение к PostgreSQL успешно!")
    
    cur = conn.cursor()
    cur.execute("SELECT version();")
    db_version = cur.fetchone()
    print(f"📦 Версия PostgreSQL: {db_version[0]}")
    
    # Проверяем наличие базы данных
    cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    databases = cur.fetchall()
    print(f"🗄️  Доступные базы данных: {[db[0] for db in databases]}")
    
    # Проверяем таблицы
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print(f"📋 Таблицы в БД {connection_params['database']}:")
    for table in tables:
        print(f"  - {table[0]}")
    
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"❌ Ошибка подключения: {e}")
    print("\n🔧 Возможные решения:")
    print("1. Убедитесь, что PostgreSQL установлен и запущен")
    print("2. Проверьте правильность логина/пароля")
    print("3. Убедитесь, что база данных существует")
    print("4. Проверьте, что порт 5432 не заблокирован брандмауэром")
except Exception as e:
    print(f"❌ Неизвестная ошибка: {e}")