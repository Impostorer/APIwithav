from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ===== АУТЕНТИФИКАЦИЯ =====
class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"

class User(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None
    is_active: bool = True
    created_at: str

class UserCreate(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    role: UserRole = UserRole.STUDENT
    
    # ДОБАВИТЬ ВАЛИДАТОР для role
    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        if isinstance(v, str):
            if v.lower() == 'teacher':
                return UserRole.TEACHER
            elif v.lower() == 'student':
                return UserRole.STUDENT
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    display_name: Optional[str] = None
    role: Optional[str] = None

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

# ===== ПРЕДМЕТЫ =====
class Subject(BaseModel):
    id: int
    title: str
    practiceCount: int
    createdAt: str  # Оставлено str, так как в БД VARCHAR(100)

class CreateSubject(BaseModel):
    title: str

class UpdateSubject(BaseModel):
    title: Optional[str] = None
    practiceCount: Optional[int] = None

# ===== ПРАКТИКИ =====
class Practice(BaseModel):
    id: int
    idSubject: int
    name: str
    numberPractice: int
    description: str
    condition: str
    createdPracticeAt: str  # Оставлено str, так как в БД VARCHAR(100)
    dateComplete: Optional[str] = None

class CreatePractice(BaseModel):
    idSubject: int
    name: str
    description: str

class UpdatePractice(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[str] = None
    dateComplete: Optional[str] = None

# ===== ЗАДАЧИ =====
class Task(BaseModel):
    id: int
    idPractice: int
    description: str
    file: str

class CreateTask(BaseModel):
    idPractice: int
    description: str
    file: str

class UpdateTask(BaseModel):
    description: Optional[str] = None
    file: Optional[str] = None

# ===== ОТПРАВКА ЗАДАНИЙ =====
class SubmissionCreate(BaseModel):
    task_id: int
    file_url: Optional[str] = None
    text_answer: Optional[str] = None

class SubmissionCheck(BaseModel):
    score: str  # любые баллы строкой
    comment: Optional[str] = None

class Submission(BaseModel):
    id: int
    student_id: int
    task_id: int
    practice_id: Optional[int] = None
    file_url: Optional[str] = None
    text_answer: Optional[str] = None
    score: Optional[str] = None
    comment: Optional[str] = None
    status: str
    submitted_at: str  # ИЗМЕНЕНО: datetime → str
    checked_at: Optional[str] = None  # ИЗМЕНЕНО: datetime → str

# ===== ФАЙЛЫ =====
class FileUploadResponse(BaseModel):
    filename: str
    url: str
    message: str