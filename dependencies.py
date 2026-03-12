from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional
from auth_service import SECRET_KEY, ALGORITHM
from models import TokenData

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    print(f"🔐 Проверка токена: {credentials.credentials[:30]}...")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        
        if not token:
            print("❌ Токен не предоставлен")
            raise credentials_exception
        
        try:
            # Декодируем токен
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print(f"✅ Токен декодирован: {payload}")
            
            user_id = payload.get("sub")
            username = payload.get("username")
            
            if not user_id or not username:
                print(f"❌ Отсутствуют обязательные поля в токене: sub={user_id}, username={username}")
                raise credentials_exception
            
            print(f"✅ User ID: {user_id}, Username: {username}")
            return TokenData(user_id=int(user_id), username=username)
            
        except jwt.ExpiredSignatureError:
            print("❌ Токен истек")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError as e:
            print(f"❌ Ошибка JWT: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except Exception as e:
        print(f"❌ Неизвестная ошибка при аутентификации: {e}")
        raise credentials_exception