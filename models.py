from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Модели для аутентификации
class User(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime

class UserCreate(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    display_name: Optional[str] = None

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

# Дополнительные модели для работы с файлами
class FileUploadResponse(BaseModel):
    filename: str
    url: str
    message: str

class TaskWithFile(BaseModel):
    id: int
    idPractice: int
    description: str
    file_url: str  # Изменено с file на file_url
    
# Subject models
class Subject(BaseModel):
    id: int
    title: str
    practiceCount: int
    createdAt: str

class CreateSubject(BaseModel):
    title: str

class UpdateSubject(BaseModel):
    title: Optional[str] = None
    practiceCount: Optional[int] = None
    condition: Optional[str] = None  # ДОБАВЛЕНО
    dateComplete: Optional[str] = None  # ДОБАВЛЕНО

# Practice models
class Practice(BaseModel):
    id: int
    idSubject: int
    name: str
    numberPractice: int
    description: str
    condition: str
    createdPracticeAt: str
    dateComplete: Optional[str] = None  # ДОБАВЛЕНО: перенесено из Task

class CreatePractice(BaseModel):
    idSubject: int
    name: str
    description: str

class UpdatePractice(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[str] = None
    dateComplete: Optional[str] = None  # ДОБАВЛЕНО

# Task models
class Task(BaseModel):
    id: int
    idPractice: int
    description: str
    file: str
    # dateComplete УДАЛЕНО: перенесено в Practice

class CreateTask(BaseModel):
    idPractice: int
    description: str
    file: str

class UpdateTask(BaseModel):
    description: Optional[str] = None
    file: Optional[str] = None
    # dateComplete УДАЛЕНО: перенесено в Practice