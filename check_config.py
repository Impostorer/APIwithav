from config import config, print_config

if __name__ == "__main__":
    print("🔍 Проверка конфигурации приложения...")
    print_config()
    
    if config.validate():
        print("✅ Конфигурация корректна!")
    else:
        print("❌ В конфигурации есть ошибки!")
        print("\nСоздайте файл .env со следующими переменными:")
        print("DB_HOST=localhost")
        print("DB_PORT=5432")
        print("DB_NAME=school_platform")
        print("DB_USER=school_user")
        print("DB_PASSWORD=your_password")