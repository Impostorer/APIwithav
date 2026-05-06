import os
from dotenv import load_dotenv
from models import SubmissionCreate, SubmissionCheck, UserRole

# ПРИНУДИТЕЛЬНАЯ загрузка .env ПЕРВОЙ строкой
load_dotenv()

print("🚀 Запуск School Platform API...")
print(f"🔑 YC_ACCESS_KEY: {'✅' if os.getenv('YC_ACCESS_KEY') else '❌'}")
print(f"🔑 YC_SECRET_KEY: {'✅' if os.getenv('YC_SECRET_KEY') else '❌'}")

from fastapi import FastAPI, HTTPException, status, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
from models import (
    Subject, Practice, Task, 
    CreateSubject, CreatePractice, CreateTask,
    UpdateSubject, UpdatePractice, UpdateTask, TokenData
)
from database import db
from file_storage import file_storage
from auth_service import auth_service
from dependencies import get_current_user
from models import UserCreate, UserLogin, Token

print("🚀 Запуск School Platform API...")

app = FastAPI(
    title="School Platform API",
    description="API для учебной платформы с полным CRUD",
    version="1.0.0"
)

JWT_SECRET = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET or JWT_SECRET == "your-super-secret-jwt-key-change-this-in-production":
    print("⚠️ ВНИМАНИЕ: JWT_SECRET_KEY не установлен или используется дефолтный!")
    print("⚠️ Для продакшена установите JWT_SECRET_KEY в .env файле")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "School Platform API", "version": "1.0.0"}

# Новые эндпоинты для аутентификации
@app.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    try:
        user_dict = auth_service.create_user(user_data)
        
        access_token = auth_service.create_access_token(
            data={
                "sub": str(user_dict["id"]),
                "username": user_dict["username"]
            }
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_dict["id"],
            "username": user_dict["username"],
            "display_name": user_dict["display_name"],
            "role": user_data.role.value  # возвращаем роль
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    user = auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен
    access_token = auth_service.create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username
        }
    )
    
    # Получаем роль пользователя
    user_role = db.get_user_role(user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user_role  
    }

@app.get("/auth/verify-token")
async def verify_token(current_user: TokenData = Depends(get_current_user)):
    """Проверить валидность токена"""
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "username": current_user.username,
        "message": "Token is valid"
    }

@app.get("/auth/verify")
async def verify_token(current_user: TokenData = Depends(get_current_user)):
    return {"valid": True, "user_id": current_user.user_id, "username": current_user.username}

@app.post("/auth/logout")
async def logout(current_user: TokenData = Depends(get_current_user)):
    # Здесь можно удалить сессию из БД, если нужно
    return {"message": "Logged out successfully"}

@app.get("/auth/me")
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    user = auth_service.get_user_by_username(current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = db.get_user_role(user['id'])
    
    return {
        "id": user['id'],
        "username": user['username'],
        "display_name": user.get('display_name'),
        "role": role,
        "created_at": user.get('created_at')
    }

@app.get("/auth/verify")
async def verify_token(current_user: TokenData = Depends(get_current_user)):
    """Проверить валидность токена"""
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "username": current_user.username,
        "message": "Token is valid"
    }

# ===== ЭНДПОИНТЫ ДЛЯ СТУДЕНТОВ =====

@app.post("/subjects/{subject_id}/subscribe")
async def subscribe_to_subject(
    subject_id: int,
    current_user: TokenData = Depends(get_current_user)
):
    """Студент подписывается на предмет"""
    role = db.get_user_role(current_user.user_id)
    if role != 'student':
        raise HTTPException(status_code=403, detail="Only students can subscribe to subjects")
    
    success = db.subscribe_student_to_subject(current_user.user_id, subject_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to subscribe")
    
    return {"message": "Successfully subscribed to subject"}

@app.delete("/subjects/{subject_id}/unsubscribe")
async def unsubscribe_from_subject(
    subject_id: int,
    current_user: TokenData = Depends(get_current_user)
):
    """Студент отписывается от предмета"""
    success = db.unsubscribe_student_from_subject(current_user.user_id, subject_id)
    return {"message": "Unsubscribed" if success else "Was not subscribed"}

@app.get("/student/subjects", response_model=List[Subject])
async def get_student_subjects(current_user: TokenData = Depends(get_current_user)):
    """Получить предметы, на которые подписан студент"""
    return db.get_student_subjects(current_user.user_id)

@app.post("/tasks/{task_id}/submit")
async def submit_task(
    task_id: int,
    submission: SubmissionCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Студент отправляет решение задачи"""
    role = db.get_user_role(current_user.user_id)
    if role != 'student':
        raise HTTPException(status_code=403, detail="Only students can submit tasks")
    
    result = db.create_submission(current_user.user_id, submission)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": "Task submitted successfully", "submission_id": result['id']}

@app.get("/student/submissions")
async def get_student_submissions(current_user: TokenData = Depends(get_current_user)):
    """Студент видит свои отправленные задания и их статус"""
    return db.get_student_submissions(current_user.user_id)

# ===== ЭНДПОИНТЫ ДЛЯ УЧИТЕЛЕЙ =====

@app.get("/teacher/subjects", response_model=List[Subject])
async def get_teacher_subjects(current_user: TokenData = Depends(get_current_user)):
    """Учитель видит свои предметы"""
    role = db.get_user_role(current_user.user_id)
    if role != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can view their subjects")
    
    return db.get_teacher_subjects(current_user.user_id)

@app.post("/subjects", response_model=Subject, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject: CreateSubject,
    current_user: TokenData = Depends(get_current_user)
):
    """Создать новый учебный предмет (только учитель)"""
    role = db.get_user_role(current_user.user_id)
    if role != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can create subjects")
    
    # Передаём teacher_id при создании
    return db.create_subject(subject, current_user.user_id)

@app.get("/teacher/pending-submissions")
async def get_pending_submissions(current_user: TokenData = Depends(get_current_user)):
    """Учитель видит непроверенные задания"""
    role = db.get_user_role(current_user.user_id)
    if role != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can check submissions")
    
    return db.get_pending_submissions(current_user.user_id)

@app.post("/submissions/{submission_id}/check")
async def check_submission(
    submission_id: int,
    check_data: SubmissionCheck,
    current_user: TokenData = Depends(get_current_user)
):
    """Учитель проверяет задание и ставит оценку"""
    role = db.get_user_role(current_user.user_id)
    if role != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can check submissions")
    
    result = db.check_submission(submission_id, check_data, current_user.user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Submission not found or not yours")
    
    return {"message": "Submission checked", "submission": result}

# ===== SUBJECTS ENDPOINTS =====
@app.get("/subjects", response_model=List[Subject])
async def get_all_subjects(current_user: TokenData = Depends(get_current_user)):
    """Получить предметы (учитель видит свои, студент - все)"""
    role = db.get_user_role(current_user.user_id)
    
    if role == 'teacher':
        return db.get_teacher_subjects(current_user.user_id)
    else:
        return db.get_all_subjects()

@app.get("/subjects/{subject_id}", response_model=Subject)
async def get_subject(subject_id: int):
    """Получить предмет по ID"""
    subject = db.get_subject_by_id(subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

@app.put("/subjects/{subject_id}", response_model=Subject)
async def update_subject(subject_id: int, subject_data: UpdateSubject):
    """Обновить учебный предмет"""
    subject = db.update_subject(subject_id, subject_data)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

@app.delete("/subjects/{subject_id}")
async def delete_subject(subject_id: int):
    """Удалить учебный предмет и все связанные данные"""
    success = db.delete_subject(subject_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {"message": "Subject deleted successfully"}

# ===== PRACTICES ENDPOINTS =====
@app.get("/practices", response_model=List[Practice])
async def get_all_practices():
    """Получить все практические работы"""
    return db.get_all_practices()

@app.get("/practices/subject/{subject_id}", response_model=List[Practice])
async def get_practices_by_subject(subject_id: int):
    """Получить практики по ID предмета"""
    return db.get_practices_by_subject_id(subject_id)

@app.get("/practices/{practice_id}", response_model=Practice)
async def get_practice(practice_id: int):
    """Получить практику по ID"""
    practice = db.get_practice_by_id(practice_id)
    if practice is None:
        raise HTTPException(status_code=404, detail="Practice not found")
    return practice

@app.post("/practices", response_model=Practice, status_code=status.HTTP_201_CREATED)
async def create_practice(practice: CreatePractice):
    """Создать новую практическую работу"""
    subject = db.get_subject_by_id(practice.idSubject)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return db.create_practice(practice)

@app.put("/practices/{practice_id}", response_model=Practice)
async def update_practice(practice_id: int, practice_data: UpdatePractice):
    """Обновить практическую работу"""
    if practice_data.condition and practice_data.condition not in ["выполнена", "не выполнена"]:
        raise HTTPException(status_code=400, detail="Condition must be 'выполнена' or 'не выполнена'")
    
    practice = db.update_practice(practice_id, practice_data)
    if practice is None:
        raise HTTPException(status_code=404, detail="Practice not found")
    return practice

@app.delete("/practices/{practice_id}")
async def delete_practice(practice_id: int):
    """Удалить практическую работу"""
    success = db.delete_practice(practice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Practice not found")
    return {"message": "Practice deleted successfully"}

@app.patch("/practices/{practice_id}/condition")
async def update_practice_condition(
    practice_id: int,
    condition_data: dict,
    current_user: TokenData = Depends(get_current_user)  # ← ДОБАВИТЬ
):
    """Обновить статус проверки практики (только учитель)"""
    role = db.get_user_role(current_user.user_id)
    if role != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can change condition")
    
    condition = condition_data.get("condition")
    
    if not condition:
        raise HTTPException(status_code=400, detail="Missing 'condition' field in request body")
    
    if condition not in ["выполнена", "не выполнена"]:
        raise HTTPException(status_code=400, detail="Condition must be 'выполнена' or 'не выполнена'")
    
    practice = db.update_practice(practice_id, UpdatePractice(condition=condition))
    
    if practice is None:
        raise HTTPException(status_code=404, detail="Practice not found")
    
    return practice

@app.patch("/practices/{practice_id}/toggle-condition")
async def toggle_practice_condition(
    practice_id: int,
    current_user: TokenData = Depends(get_current_user)  # ← ДОБАВИТЬ
):
    """Переключить статус проверки практики (только учитель)"""
    role = db.get_user_role(current_user.user_id)
    if role != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can change condition")
    
    practice = db.get_practice_by_id(practice_id)
    if practice is None:
        raise HTTPException(status_code=404, detail="Practice not found")
    
    new_condition = "выполнена" if practice.condition == "не выполнена" else "не выполнена"
    
    updated_practice = db.update_practice(practice_id, UpdatePractice(condition=new_condition))
    return updated_practice

@app.patch("/practices/{practice_id}/complete")
async def complete_practice(
    practice_id: int,
    current_user: TokenData = Depends(get_current_user)  # ← ДОБАВИТЬ
):
    """Отметить практику как выполненную (только учитель)"""
    role = db.get_user_role(current_user.user_id)
    if role != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can complete practices")
    
    practice = db.complete_practice(practice_id)
    if practice is None:
        raise HTTPException(status_code=404, detail="Practice not found")
    return practice

@app.post("/practices/{practice_id}/toggle")
async def toggle_practice_status(
    practice_id: int,
    current_user: TokenData = Depends(get_current_user)  # ← ДОБАВИТЬ
):
    """Простой переключатель статуса практики (только учитель)"""
    role = db.get_user_role(current_user.user_id)
    if role != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can toggle status")
    
    try:
        practice = db.get_practice_by_id(practice_id)
        if practice is None:
            raise HTTPException(status_code=404, detail="Practice not found")
        
        new_condition = "выполнена" if practice.condition == "не выполнена" else "не выполнена"
        
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE practices SET condition = %s WHERE id = %s RETURNING *",
                    (new_condition, practice_id)
                )
                result = cur.fetchone()
                conn.commit()
                
                if result:
                    return {
                        "id": result['id'],
                        "condition": result['condition'],
                        "message": f"Status changed to {result['condition']}"
                    }
                else:
                    raise HTTPException(status_code=500, detail="Failed to update practice")
                    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== TASKS ENDPOINTS =====
@app.get("/tasks", response_model=List[Task])
async def get_all_tasks():
    """Получить все задачи"""
    return db.get_all_tasks()

@app.get("/tasks/practice/{practice_id}", response_model=List[Task])
async def get_tasks_by_practice(practice_id: int):
    """Получить задачи по ID практики"""
    return db.get_tasks_by_practice_id(practice_id)

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int):
    """Получить задачу по ID"""
    task = db.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task: CreateTask):
    """Создать новую задачу"""
    practice = db.get_practice_by_id(task.idPractice)
    if practice is None:
        raise HTTPException(status_code=404, detail="Practice not found")
    return db.create_task(task)

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task_data: UpdateTask):
    """Обновить задачу"""
    task = db.update_task(task_id, task_data)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Удалить задачу"""
    success = db.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

# ===== FILES ENDPOINTS =====

@app.post("/upload-file/")
async def upload_file(file: UploadFile = File(...)):
    """Загрузить файл в Yandex Cloud S3 (оригинальный endpoint)"""
    try:
        file_url = await file_storage.upload_file(file)
        return {
            "filename": file.filename,
            "url": file_url,
            "message": "Файл успешно загружен"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-file-bytes/")
async def upload_file_bytes(
    file: bytes = File(...),
    filename: str = Form(...)
):
    """Загрузить файл в виде bytes (новый endpoint для Flutter)"""
    try:
        # Определяем Content-Type по расширению файла
        content_type = "application/octet-stream"
        file_lower = filename.lower()
        
        if file_lower.endswith('.pdf'):
            content_type = "application/pdf"
        elif file_lower.endswith('.doc'):
            content_type = "application/msword"
        elif file_lower.endswith('.docx'):
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif file_lower.endswith('.xls'):
            content_type = "application/vnd.ms-excel"
        elif file_lower.endswith('.xlsx'):
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif file_lower.endswith('.txt'):
            content_type = "text/plain"
        
        file_url = await file_storage.upload_file_bytes(file, filename, content_type)
        return {
            "filename": filename,
            "url": file_url,
            "message": "Файл успешно загружен"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete-file/")
async def delete_file(file_url: str):
    """Удалить файл из Yandex Cloud S3"""
    success = await file_storage.delete_file(file_url)
    if success:
        return {"message": "Файл успешно удален"}
    else:
        raise HTTPException(status_code=500, detail="Ошибка при удалении файла")

@app.post("/tasks-with-file", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task_with_file(
    task_data: CreateTask,
    file: Optional[UploadFile] = None
):
    """Создать новую задачу с загрузкой файла"""
    practice = db.get_practice_by_id(task_data.idPractice)
    if practice is None:
        raise HTTPException(status_code=404, detail="Practice not found")
    
    # Если передан файл, загружаем его в S3
    if file:
        file_url = await file_storage.upload_file(file)
        # Создаем задачу с URL файла
        task_with_file = CreateTask(
            idPractice=task_data.idPractice,
            description=task_data.description,
            file=file_url
        )
        return db.create_task(task_with_file)
    else:
        return db.create_task(task_data)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {"status": "healthy", "service": "school-platform-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)