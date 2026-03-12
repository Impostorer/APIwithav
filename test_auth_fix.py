import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    print("🚀 Тестирование аутентификации и создания предмета...")
    
    # 1. Логин
    print("\n1. 🔐 Логин...")
    login_data = {
        "username": "danil",
        "password": "123456"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ Логин не удался: {response.text}")
        return None
    
    token_data = response.json()
    token = token_data["access_token"]
    print(f"   ✅ Токен получен: {token[:30]}...")
    print(f"   👤 User ID: {token_data['user_id']}")
    print(f"   📛 Username: {token_data['username']}")
    
    # 2. Проверка токена
    print("\n2. 🔍 Проверка токена...")
    headers = {"Authorization": f"Bearer {token}"}
    verify_response = requests.get(f"{BASE_URL}/auth/verify-token", headers=headers)
    print(f"   Status: {verify_response.status_code}")
    print(f"   Response: {verify_response.text}")
    
    # 3. Создание предмета
    print("\n3. 📚 Создание предмета...")
    subject_data = {"title": "Тестовый предмет"}
    subject_response = requests.post(
        f"{BASE_URL}/subjects", 
        json=subject_data, 
        headers=headers
    )
    print(f"   Status: {subject_response.status_code}")
    print(f"   Response: {subject_response.text}")
    
    if subject_response.status_code == 201:
        print("   ✅ Предмет успешно создан!")
    else:
        print("   ❌ Ошибка создания предмета")
    
    return token

if __name__ == "__main__":
    test_auth_flow()