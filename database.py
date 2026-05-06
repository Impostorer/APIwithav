# database.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Optional
from models import (
    Subject, Practice, Task, 
    CreateSubject, CreatePractice, CreateTask, 
    UpdateSubject, UpdatePractice, UpdateTask,
    SubmissionCreate, SubmissionCheck  # ← ДОБАВЛЕНО
)

class PostgreSQLDatabase:
    def __init__(self):
        # Параметры подключения из .env файла
        self.connection_string = f"postgresql://{os.getenv('DB_USER', 'student')}:{os.getenv('DB_PASSWORD', '12345')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'practiceHub')}"
    
    def get_connection(self):
        """Получить соединение с базой данных"""
        return psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)
    
    def _get_current_date(self) -> str:
        """Получить текущую дату в формате YYYY-MM-DD для PostgreSQL"""
        return datetime.now().strftime("%Y-%m-%d")

    # ===== USERS =====
    def get_user_role(self, user_id: int) -> Optional[str]:
        """Получить роль пользователя"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
                result = cur.fetchone()
                return result['role'] if result else None

    # ===== SUBJECTS CRUD =====
    def get_all_subjects(self) -> List[Subject]:
        """Получить все предметы"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM subjects ORDER BY id")
                results = cur.fetchall()
                return [Subject(
                    id=row['id'],
                    title=row['title'],
                    practiceCount=row['practice_count'],
                    createdAt=row['created_at']
                ) for row in results]

    def get_subject_by_id(self, subject_id: int) -> Optional[Subject]:
        """Получить предмет по ID"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM subjects WHERE id = %s", (subject_id,))
                result = cur.fetchone()
                if result:
                    return Subject(
                        id=result['id'],
                        title=result['title'],
                        practiceCount=result['practice_count'],
                        createdAt=result['created_at']
                    )
                return None

    def create_subject(self, subject_data: CreateSubject, user_id: Optional[int] = None) -> Subject:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                current_date = datetime.now().strftime("%Y-%m-%d")
            
                if user_id:
                    cur.execute(
                        "INSERT INTO subjects (title, practice_count, created_at, teacher_id) VALUES (%s, %s, %s, %s) RETURNING *",
                        (subject_data.title, 0, current_date, user_id)
                    )
                else:
                    cur.execute(
                        "INSERT INTO subjects (title, practice_count, created_at) VALUES (%s, %s, %s) RETURNING *",
                        (subject_data.title, 0, current_date)
                    )  
            
                result = cur.fetchone()
                conn.commit()
                return Subject(
                    id=result['id'],
                    title=result['title'],
                    practiceCount=result['practice_count'],
                    createdAt=result['created_at']
                )

    def update_subject(self, subject_id: int, subject_data: UpdateSubject) -> Optional[Subject]:
        """Обновить предмет"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                update_fields = []
                values = []
                
                if subject_data.title is not None:
                    update_fields.append("title = %s")
                    values.append(subject_data.title)
                
                if subject_data.practiceCount is not None:
                    update_fields.append("practice_count = %s")
                    values.append(subject_data.practiceCount)
                
                if not update_fields:
                    return self.get_subject_by_id(subject_id)
                
                values.append(subject_id)
                query = f"UPDATE subjects SET {', '.join(update_fields)} WHERE id = %s RETURNING *"
                
                cur.execute(query, values)
                result = cur.fetchone()
                conn.commit()
                
                if result:
                    return Subject(
                        id=result['id'],
                        title=result['title'],
                        practiceCount=result['practice_count'],
                        createdAt=result['created_at']
                    )
                return None

    def delete_subject(self, subject_id: int) -> bool:
        """Удалить предмет и все связанные практики и задачи"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
                conn.commit()
                return cur.rowcount > 0

    def update_subject_practice_count(self, subject_id: int):
        """Обновить счетчик практик для предмета"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE subjects SET practice_count = (SELECT COUNT(*) FROM practices WHERE subject_id = %s) WHERE id = %s",
                    (subject_id, subject_id)
                )
                conn.commit()

    # ===== SUBSCRIPTIONS =====
    def subscribe_student_to_subject(self, student_id: int, subject_id: int) -> bool:
        """Подписка студента на предмет"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """INSERT INTO student_subjects (student_id, subject_id) 
                        VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING id""",
                        (student_id, subject_id)
                    )
                    conn.commit()
                    return cur.fetchone() is not None
                except Exception as e:
                    print(f"Error subscribing: {e}")
                    return False

    def unsubscribe_student_from_subject(self, student_id: int, subject_id: int) -> bool:
        """Отписка студента от предмета"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM student_subjects WHERE student_id = %s AND subject_id = %s",
                    (student_id, subject_id)
                )
                conn.commit()
                return cur.rowcount > 0

    def get_student_subjects(self, student_id: int) -> List[Subject]:
        """Получить предметы, на которые подписан студент"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT s.* FROM subjects s
                    JOIN student_subjects ss ON s.id = ss.subject_id
                    WHERE ss.student_id = %s
                    ORDER BY s.id
                """, (student_id,))
                results = cur.fetchall()
                return [Subject(
                    id=row['id'],
                    title=row['title'],
                    practiceCount=row['practice_count'],
                    createdAt=row['created_at']
                ) for row in results]

    def get_teacher_subjects(self, teacher_id: int) -> List[Subject]:
        """Получить предметы, созданные учителем"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM subjects WHERE teacher_id = %s ORDER BY id",
                    (teacher_id,)
                )
                results = cur.fetchall()
                return [Subject(
                    id=row['id'],
                    title=row['title'],
                    practiceCount=row['practice_count'],
                    createdAt=row['created_at']
                ) for row in results]

    def is_student_subscribed(self, student_id: int, subject_id: int) -> bool:
        """Проверить, подписан ли студент на предмет"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM student_subjects WHERE student_id = %s AND subject_id = %s",
                    (student_id, subject_id)
                )
                return cur.fetchone() is not None

    # ===== PRACTICES CRUD =====
    def get_all_practices(self) -> List[Practice]:
        """Получить все практики"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM practices ORDER BY id")
                results = cur.fetchall()
                return [Practice(
                    id=row['id'],
                    idSubject=row['subject_id'],
                    name=row['name'],
                    numberPractice=row['number_practice'],
                    description=row['description'],
                    condition=row['condition'],
                    createdPracticeAt=row['created_at'],
                    dateComplete=row['date_complete']
                ) for row in results]

    def get_practices_by_subject_id(self, subject_id: int) -> List[Practice]:
        """Получить практики по ID предмета"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM practices WHERE subject_id = %s ORDER BY number_practice", (subject_id,))
                results = cur.fetchall()
                return [Practice(
                    id=row['id'],
                    idSubject=row['subject_id'],
                    name=row['name'],
                    numberPractice=row['number_practice'],
                    description=row['description'],
                    condition=row['condition'],
                    createdPracticeAt=row['created_at'],
                    dateComplete=row['date_complete']
                ) for row in results]

    def get_practice_by_id(self, practice_id: int) -> Optional[Practice]:
        """Получить практику по ID"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM practices WHERE id = %s", (practice_id,))
                result = cur.fetchone()
                if result:
                    return Practice(
                        id=result['id'],
                        idSubject=result['subject_id'],
                        name=result['name'],
                        numberPractice=result['number_practice'],
                        description=result['description'],
                        condition=result['condition'],
                        createdPracticeAt=result['created_at'],
                        dateComplete=result['date_complete']
                    )
                return None

    def create_practice(self, practice_data: CreatePractice) -> Practice:
        """Создать новую практику"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Получаем следующий номер практики для этого предмета
                cur.execute("SELECT COALESCE(MAX(number_practice), 0) + 1 as next_number FROM practices WHERE subject_id = %s", 
                        (practice_data.idSubject,))
                next_number_result = cur.fetchone()
                next_number = next_number_result['next_number'] if next_number_result else 1

                # Используем правильный формат даты
                current_date = self._get_current_date()
            
                cur.execute(
                    """INSERT INTO practices (subject_id, name, number_practice, description, condition, created_at, date_complete) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                    (practice_data.idSubject, practice_data.name, next_number, practice_data.description, 
                    "не выполнена", current_date, None)
                )
                result = cur.fetchone()
                conn.commit()
            
                # Обновляем счетчик практик в предмете
                self.update_subject_practice_count(practice_data.idSubject)
            
                return Practice(
                    id=result['id'],
                    idSubject=result['subject_id'],
                    name=result['name'],
                    numberPractice=result['number_practice'],
                    description=result['description'],
                    condition=result['condition'],
                    createdPracticeAt=result['created_at'],
                    dateComplete=result['date_complete']
                )

    def update_practice(self, practice_id: int, practice_data: UpdatePractice) -> Optional[Practice]:
        """Обновить практику"""
        print(f"DEBUG: Updating practice {practice_id} with data: {practice_data}")
    
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                update_fields = []
                values = []
                
                if practice_data.name is not None:
                    update_fields.append("name = %s")
                    values.append(practice_data.name)
                
                if practice_data.description is not None:
                    update_fields.append("description = %s")
                    values.append(practice_data.description)
                
                if practice_data.condition is not None:
                    update_fields.append("condition = %s")
                    values.append(practice_data.condition)
                
                if practice_data.dateComplete is not None:
                    update_fields.append("date_complete = %s")
                    values.append(practice_data.dateComplete)
                
                if not update_fields:
                    return self.get_practice_by_id(practice_id)
                
                values.append(practice_id)
                query = f"UPDATE practices SET {', '.join(update_fields)} WHERE id = %s RETURNING *"
                
                cur.execute(query, values)
                result = cur.fetchone()
                conn.commit()
                
                if result:
                    return Practice(
                        id=result['id'],
                        idSubject=result['subject_id'],
                        name=result['name'],
                        numberPractice=result['number_practice'],
                        description=result['description'],
                        condition=result['condition'],
                        createdPracticeAt=result['created_at'],
                        dateComplete=result['date_complete']
                    )
                return None

    def delete_practice(self, practice_id: int) -> bool:
        """Удалить практику и все связанные задачи"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Находим subject_id для обновления счетчика
                cur.execute("SELECT subject_id FROM practices WHERE id = %s", (practice_id,))
                practice = cur.fetchone()
                
                cur.execute("DELETE FROM practices WHERE id = %s", (practice_id,))
                deleted = cur.rowcount > 0
                conn.commit()
                
                # Обновляем счетчик практик в предмете
                if practice and deleted:
                    self.update_subject_practice_count(practice['subject_id'])
                
                return deleted

    def complete_practice(self, practice_id: int) -> Optional[Practice]:
        """Отметить практику как выполненную"""
        return self.update_practice(practice_id, UpdatePractice(dateComplete=self._get_current_date()))

    # ===== TASKS CRUD =====
    def get_all_tasks(self) -> List[Task]:
        """Получить все задачи"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tasks ORDER BY id")
                results = cur.fetchall()
                return [Task(
                    id=row['id'],
                    idPractice=row['practice_id'],
                    description=row['description'],
                    file=row['file']
                ) for row in results]

    def get_tasks_by_practice_id(self, practice_id: int) -> List[Task]:
        """Получить задачи по ID практики"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tasks WHERE practice_id = %s ORDER BY id", (practice_id,))
                results = cur.fetchall()
                return [Task(
                    id=row['id'],
                    idPractice=row['practice_id'],
                    description=row['description'],
                    file=row['file']
                ) for row in results]

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Получить задачу по ID"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
                result = cur.fetchone()
                if result:
                    return Task(
                        id=result['id'],
                        idPractice=result['practice_id'],
                        description=result['description'],
                        file=result['file']
                    )
                return None

    def create_task(self, task_data: CreateTask) -> Task:
        """Создать новую задачу"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tasks (practice_id, description, file) VALUES (%s, %s, %s) RETURNING *",
                    (task_data.idPractice, task_data.description, task_data.file)
                )
                result = cur.fetchone()
                conn.commit()
                return Task(
                    id=result['id'],
                    idPractice=result['practice_id'],
                    description=result['description'],
                    file=result['file']
                )

    def update_task(self, task_id: int, task_data: UpdateTask) -> Optional[Task]:
        """Обновить задачу"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                update_fields = []
                values = []
                
                if task_data.description is not None:
                    update_fields.append("description = %s")
                    values.append(task_data.description)
                
                if task_data.file is not None:
                    update_fields.append("file = %s")
                    values.append(task_data.file)
                
                if not update_fields:
                    return self.get_task_by_id(task_id)
                
                values.append(task_id)
                query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = %s RETURNING *"
                
                cur.execute(query, values)
                result = cur.fetchone()
                conn.commit()
                
                if result:
                    return Task(
                        id=result['id'],
                        idPractice=result['practice_id'],
                        description=result['description'],
                        file=result['file']
                    )
                return None

    def delete_task(self, task_id: int) -> bool:
        """Удалить задачу"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
                conn.commit()
                return cur.rowcount > 0

    # ===== SUBMISSIONS =====
    def create_submission(self, student_id: int, submission: SubmissionCreate) -> Optional[dict]:
        """Студент отправляет задание на проверку"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Получаем practice_id из задачи
                cur.execute("SELECT practice_id FROM tasks WHERE id = %s", (submission.task_id,))
                task = cur.fetchone()
                if not task:
                    return None
                
                cur.execute(
                    """INSERT INTO submissions 
                    (student_id, task_id, practice_id, file_url, text_answer) 
                    VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                    (student_id, submission.task_id, task['practice_id'], 
                     submission.file_url, submission.text_answer)
                )
                result = cur.fetchone()
                conn.commit()
                return dict(result)

    def check_submission(self, submission_id: int, check_data: SubmissionCheck, teacher_id: int) -> Optional[dict]:
        """Учитель проверяет задание (только свои предметы)"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Проверяем, что учитель имеет право проверять это задание
                cur.execute("""
                    SELECT s.teacher_id 
                    FROM submissions sb
                    JOIN practices p ON sb.practice_id = p.id
                    JOIN subjects s ON p.subject_id = s.id
                    WHERE sb.id = %s
                """, (submission_id,))
                result = cur.fetchone()
                
                if not result or result['teacher_id'] != teacher_id:
                    return None
                
                cur.execute(
                    """UPDATE submissions 
                    SET score = %s, comment = %s, status = 'checked', checked_at = CURRENT_TIMESTAMP 
                    WHERE id = %s RETURNING *""",
                    (check_data.score, check_data.comment, submission_id)
                )
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None

    def get_pending_submissions(self, teacher_id: int) -> List[dict]:
        """Получить непроверенные задания для учителя"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT sb.*, t.description as task_description, 
                           p.name as practice_name, u.username as student_name
                    FROM submissions sb
                    JOIN tasks t ON sb.task_id = t.id
                    JOIN practices p ON sb.practice_id = p.id
                    JOIN subjects s ON p.subject_id = s.id
                    JOIN users u ON sb.student_id = u.id
                    WHERE s.teacher_id = %s AND sb.status = 'pending'
                    ORDER BY sb.submitted_at DESC
                """, (teacher_id,))
                return [dict(row) for row in cur.fetchall()]

    def get_student_submissions(self, student_id: int) -> List[dict]:
        """Получить свои отправленные задания (для студента)"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT sb.*, t.description as task_description, 
                           p.name as practice_name
                    FROM submissions sb
                    JOIN tasks t ON sb.task_id = t.id
                    JOIN practices p ON sb.practice_id = p.id
                    WHERE sb.student_id = %s
                    ORDER BY sb.submitted_at DESC
                """, (student_id,))
                return [dict(row) for row in cur.fetchall()]

# Создаем глобальный экземпляр базы данных
db = PostgreSQLDatabase()