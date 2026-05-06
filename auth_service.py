import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from models import User, TokenData, UserCreate
import psycopg2
from psycopg2.extras import RealDictCursor

# Конфигурация JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

class AuthService:
    def __init__(self):
        self.connection_string = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    
    def verify_password(self, plain_password: str, stored_password: str) -> bool:
        """Простая проверка пароля без хеширования"""
        return plain_password == stored_password
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
        # Конвертируем datetime в timestamp (int)
        to_encode.update({"exp": int(expire.timestamp())})
    
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def save_user_session(self, user_id: int, token: str):
        """Сохраняем сессию в БД (опционально, для возможности принудительного разлогина)"""
        with psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                cur.execute(
                    "INSERT INTO user_sessions (user_id, token, expires_at) VALUES (%s, %s, %s)",
                    (user_id, token, expires_at)
                )
                conn.commit()
    
    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Получить пользователя по имени (включая пароль в чистом виде)"""
        print(f"🔍 Поиск пользователя: {username}")
        try:
            with psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # Получаем все данные за один запрос, включая role
                    cur.execute("""
                        SELECT id, username, password, display_name, is_active, created_at, role 
                        FROM users WHERE username = %s
                    """, (username,))
                    result = cur.fetchone()
                    
                    if result:
                        print(f"✅ Найден пользователь: {result['username']}, роль: {result.get('role')}")
                        return dict(result)
                    else:
                        print(f"❌ Пользователь {username} не найден")
                        return None
                        
        except Exception as e:
            print(f"🔥 Ошибка подключения к БД: {e}")
            import traceback
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            return None
    
    def _convert_user_dict(self, user_dict: dict) -> dict:
        """Конвертирует datetime поля в строки для совместимости с Pydantic"""
        result = dict(user_dict)
        if 'created_at' in result and isinstance(result['created_at'], datetime):
            result['created_at'] = result['created_at'].isoformat()
        return result
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя с простой проверкой пароля"""
        print(f"🔍 Аутентификация: {username}")
        
        try:
            # Получаем данные пользователя
            user_dict = self.get_user_by_username(username)
            
            if not user_dict:
                print(f"❌ Пользователь {username} не найден")
                return None
            
            print(f"🔍 Пароль из БД: {user_dict.get('password')}")
            print(f"🔍 Введенный пароль: {password}")
            
            # Простая проверка пароля
            if not self.verify_password(password, user_dict['password']):
                print(f"❌ Неверный пароль для {username}")
                return None
            
            print(f"✅ Аутентификация успешна для {username}")
            
            # Конвертируем datetime поля в строки
            user_dict = self._convert_user_dict(user_dict)
            
            # Создаем объект User без пароля
            return User(
                id=user_dict['id'],
                username=user_dict['username'],
                display_name=user_dict.get('display_name'),
                is_active=user_dict.get('is_active', True),
                created_at=user_dict['created_at']
            )
            
        except Exception as e:
            print(f"🔥 Ошибка в authenticate_user: {e}")
            import traceback
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            return None
    
    def create_user(self, user_data: UserCreate) -> User:
        """Создать нового пользователя с ролью"""
        print(f"📝 Создание пользователя: {user_data.username} с ролью {user_data.role}")
        
        try:
            with psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # Проверяем, существует ли пользователь
                    cur.execute("SELECT id FROM users WHERE username = %s", (user_data.username,))
                    if cur.fetchone():
                        raise HTTPException(status_code=400, detail="Username already exists")
                
                    # Сохраняем с ролью
                    cur.execute(
                        """INSERT INTO users (username, password, display_name, role) 
                        VALUES (%s, %s, %s, %s) 
                        RETURNING id, username, display_name, is_active, created_at""",
                        (user_data.username, user_data.password, 
                        user_data.display_name, user_data.role.value)
                    )
                    result = cur.fetchone()
                    conn.commit()
                    
                    print(f"✅ Пользователь {user_data.username} создан с ID: {result['id']}")
                    
                    # Конвертируем datetime поля в строки
                    user_dict = self._convert_user_dict(dict(result))
                    
                    return User(**user_dict)
                    
        except HTTPException:
            raise
        except Exception as e:
            print(f"🔥 Ошибка создания пользователя: {e}")
            import traceback
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_user_session(self, token: str) -> bool:
        """Удаляем сессию (при выходе)"""
        with psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_sessions WHERE token = %s", (token,))
                conn.commit()
                return cur.rowcount > 0

auth_service = AuthService()