import requests
import json

BASE_URL = "http://localhost:8000"

def test_full_flow():
    print("🚀 Полное тестирование аутентификации...")
    
    # Шаг 1: Регистрация
    print("\n1. 📝 Регистрация пользователя...")
    register_data = {
        "username": "test_user_123",
        "password": "test123",
        "display_name": "Test User"
    }
    
    reg_response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"   Статус: {reg_response.status_code}")
    if reg_response.status_code == 200:
        print("   ✅ Регистрация успешна")
        token = reg_response.json()["access_token"]
    else:
        print(f"   ⚠️ Регистрация не удалась: {reg_response.text}")
        print("   🔄 Пробуем логин...")
        
        # Шаг 1а: Логин если пользователь уже существует
        login_data = {
            "username": "test_user_123",
            "password": "test123"
        }
        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"   Логин статус: {login_response.status_code}")
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
        else:
            print(f"   ❌ Логин тоже не удался: {login_response.text}")
            return
    
    print(f"\n2. 🔐 Получен токен: {token[:30]}...")
    
    # Шаг 2: Проверка токена через /auth/me
    print("\n3. 🔍 Проверка токена через /auth/me...")
    headers = {"Authorization": f"Bearer {token}"}
    me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"   Статус: {me_response.status_code}")
    print(f"   Ответ: {me_response.text}")
    
    # Шаг 3: Создание предмета
    print("\n4. 📚 Создание предмета...")
    subject_data = {"title": "Математика"}
    subject_response = requests.post(
        f"{BASE_URL}/subjects", 
        json=subject_data, 
        headers=headers
    )
    print(f"   Статус: {subject_response.status_code}")
    print(f"   Ответ: {subject_response.text}")
    
    # Шаг 4: Получение списка предметов
    print("\n5. 📋 Получение всех предметов...")
    subjects_response = requests.get(f"{BASE_URL}/subjects", headers=headers)
    print(f"   Статус: {subjects_response.status_code}")
    if subjects_response.status_code == 200:
        subjects = subjects_response.json()
        print(f"   ✅ Предметов в БД: {len(subjects)}")
        for subject in subjects:
            print(f"      - {subject['title']} (ID: {subject['id']})")
    else:
        print(f"   ❌ Ошибка: {subjects_response.text}")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_full_flow()