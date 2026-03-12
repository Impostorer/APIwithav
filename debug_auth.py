import requests
import json

BASE_URL = "http://localhost:8000"

def debug_auth():
    print("🔍 Отладка аутентификации...")
    
    # 1. Логин
    print("\n1. 🔐 Пробуем логин...")
    login_data = {
        "username": "student",
        "password": "123456"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"   ✅ Успешно!")
            print(f"   Token: {json.dumps(token_data, indent=2, ensure_ascii=False)}")
            
            # 2. Проверяем что токен валиден
            token = token_data["access_token"]
            print(f"\n2. 🔍 Анализ токена...")
            print(f"   Длина токена: {len(token)} символов")
            print(f"   Начало токена: {token[:50]}...")
            
            # 3. Пробуем использовать токен
            print(f"\n3. 🚀 Используем токен для создания предмета...")
            headers = {"Authorization": f"Bearer {token}"}
            subject_data = {"title": "Тестовый предмет"}
            
            try:
                subject_response = requests.post(
                    f"{BASE_URL}/subjects", 
                    json=subject_data, 
                    headers=headers,
                    timeout=10
                )
                print(f"   Status: {subject_response.status_code}")
                print(f"   Response: {subject_response.text}")
            except Exception as e:
                print(f"   ❌ Ошибка при создании предмета: {e}")
                
        else:
            print(f"   ❌ Ошибка: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    debug_auth()