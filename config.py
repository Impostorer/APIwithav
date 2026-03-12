import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных PostgreSQL"""
    host: str = "localhost"
    port: int = 5432
    database: str = "practiceHub"
    username: str = "student"
    password: str = "12345"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800

    def __post_init__(self):
        """Загружаем значения из переменных окружения после инициализации"""
        self.host = os.getenv("DB_HOST", self.host)
        self.port = int(os.getenv("DB_PORT", str(self.port)))
        self.database = os.getenv("DB_NAME", self.database)
        self.username = os.getenv("DB_USER", self.username)
        self.password = os.getenv("DB_PASSWORD", self.password)
        self.pool_size = int(os.getenv("DB_POOL_SIZE", str(self.pool_size)))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", str(self.max_overflow)))

    @property
    def connection_string(self) -> str:
        """Строка подключения для SQLAlchemy"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_connection_string(self) -> str:
        """Асинхронная строка подключения для asyncpg"""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def validate(self) -> bool:
        """Проверка, что все обязательные параметры установлены"""
        required_vars = {
            "DB_HOST": self.host,
            "DB_PORT": self.port,
            "DB_NAME": self.database,
            "DB_USER": self.username,
            "DB_PASSWORD": self.password,
        }
        
        missing = [key for key, value in required_vars.items() if not value]
        if missing:
            print(f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing)}")
            return False
        
        print("✅ Все обязательные переменные окружения установлены")
        return True


@dataclass
class AppConfig:
    """Конфигурация приложения"""
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    log_level: str = "info"

    def __post_init__(self):
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.host = os.getenv("APP_HOST", self.host)
        self.port = int(os.getenv("APP_PORT", str(self.port)))
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        
        # Обработка CORS origins
        cors_origins_str = os.getenv("CORS_ORIGINS", "")
        if cors_origins_str:
            self.cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]


@dataclass
class Config:
    """Основной класс конфигурации"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    app: AppConfig = field(default_factory=AppConfig)

    def validate(self) -> bool:
        """Проверка всей конфигурации"""
        print("🔍 Проверка конфигурации...")
        print(f"   Host: {self.database.host}")
        print(f"   Port: {self.database.port}")
        print(f"   Database: {self.database.database}")
        print(f"   Username: {self.database.username}")
        print(f"   Password: {'*' * len(self.database.password) if self.database.password else 'NOT SET'}")
        
        return self.database.validate()


# Глобальный экземпляр конфигурации
config = Config()


def print_config():
    """Печать текущей конфигурации (без пароля)"""
    print("📋 Текущая конфигурация:")
    print(f"   Database: {config.database.host}:{config.database.port}/{config.database.database}")
    print(f"   Username: {config.database.username}")
    print(f"   Password: {'*' * len(config.database.password) if config.database.password else 'NOT SET'}")
    print(f"   App: {config.app.host}:{config.app.port}")
    print(f"   Debug: {config.app.debug}")
    print(f"   CORS Origins: {config.app.cors_origins}")


if __name__ == "__main__":
    # При прямом запуске файла показываем конфигурацию
    print_config()
    config.validate()