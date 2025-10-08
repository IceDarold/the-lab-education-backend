
### **API v1 — Проектирование Эндпоинтов**

**Базовый URL:** `/api/v1`

---

### **Ресурс: `Auth` (Аутентификация)**
* **Роутер:** `/auth`

#### **1. Регистрация**
* **Эндпоинт:** `POST /auth/register`
* **Назначение:** Создание нового пользователя.
* **Аутентификация:** Не требуется.
* **Request Body (Схема Pydantic `UserCreate`):**
  ```json
  {
    "full_name": "Алексей Петров",
    "email": "alexey.p@email.com",
    "password": "supersecretpassword123"
  }
  ```
* **Success Response (201 Created) (Схема `Token`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

#### **2. Вход (Получение токена)**
* **Эндпоинт:** `POST /auth/login`
* **Назначение:** Аутентификация пользователя и выдача JWT-токена.
* **Аутентификация:** Не требуется.
* **Request Body (Форма OAuth2):** `username` (будет `email`) и `password`.
* **Success Response (200 OK) (Схема `Token`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

#### **3. Получение данных о себе**
* **Эндпоинт:** `GET /auth/me`
* **Назначение:** Получение информации о текущем залогиненном пользователе.
* **Аутентификация:** **Требуется (Bearer Token)**.
* **Request Body:** Нет.
* **Success Response (200 OK) (Схема `User`):**
  ```json
  {
    "user_id": "uuid-goes-here",
    "full_name": "Алексей Петров",
    "email": "alexey.p@email.com"
  }
  ```
#### **4. Проверка существования email**
* **Эндпоинт:** `POST /auth/check-email`
* **Назначение:** Проверить, существует ли email в системе.
* **Аутентификация:** Не требуется.
* **Request Body (Схема `CheckEmailRequest`):**
  ```json
  {
    "email": "user@example.com"
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "exists": true
  }
  ```

#### **5. Запрос на сброс пароля**
* **Эндпоинт:** `POST /auth/forgot-password`
* **Назначение:** Отправить email для сброса пароля.
* **Аутентификация:** Не требуется.
* **Request Body (Схема `ForgotPasswordRequest`):**
  ```json
  {
    "email": "user@example.com"
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "message": "Password reset email sent"
  }
  ```

#### **6. Сброс пароля**
* **Эндпоинт:** `POST /auth/reset-password`
* **Назначение:** Сбросить пароль с использованием токена.
* **Аутентификация:** Не требуется.
* **Request Body (Схема `ResetPasswordRequest`):**
  ```json
  {
    "token": "recovery_token",
    "newPassword": "newpassword123"
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "message": "Password updated successfully"
  }
  ```

---

### **Ресурс: `Courses` (Курсы)**
* **Роутер:** `/courses`

#### **1. Получение списка всех курсов (для публичного каталога)**
* **Эндпоинт:** `GET /courses`
* **Назначение:** Отображение всех доступных курсов на платформе.
* **Аутентификация:** Не требуется.
* **Request Body:** Нет.
* **Success Response (200 OK) (Список схем `CoursePublic`):**
  ```json
  [
    {
      "course_id": "uuid-course-1",
      "slug": "classic-machine-learning",
      "title": "Классическое Машинное Обучение",
      "description": "Изучите мощные алгоритмы...",
      "cover_image_url": "https://.../cover1.png"
    },
    ...
  ]
  ```

#### **2. Получение детальной информации о курсе (для публичной страницы)**
* **Эндпоинт:** `GET /courses/{slug}`
* **Назначение:** Показать детальную программу курса для незаписанного пользователя.
* **Аутентификация:** Не требуется.
* **Request Body:** Нет.
* **Success Response (200 OK) (Схема `CourseDetailsPublic`):**
  ```json
  {
    "course_id": "uuid-course-1",
    "slug": "classic-machine-learning",
    "title": "Классическое Машинное Обучение",
    "description": "...",
    "cover_image_url": "...",
    "modules": [
      {
        "title": "Часть 1: Введение в Мир ML",
        "lessons": [
          { "title": "Урок 1: Что такое ML?" },
          { "title": "Урок 2: Инструментарий Аналитика" }
        ]
      },
      ...
    ]
  }
  ```

#### **3. Запись на курс**
* **Эндпоинт:** `POST /courses/{slug}/enroll`
* **Назначение:** Записать текущего пользователя на курс.
* **Аутентификация:** **Требуется**.
* **Request Body:** Нет.
* **Success Response (201 Created):** Пустое тело ответа.

---

### **Ресурс: `Dashboard` (Личный кабинет пользователя)**
* **Роутер:** `/dashboard`

#### **1. Получение курсов пользователя**
* **Эндпоинт:** `GET /dashboard/my-courses`
* **Назначение:** Главный запрос для дашборда, получает список курсов пользователя с его прогрессом.
* **Аутентификация:** **Требуется**.
* **Request Body:** Нет.
* **Success Response (200 OK) (Список схем `CourseWithProgress`):**
  ```json
  [
    {
      "course_id": "uuid-course-1",
      "slug": "classic-machine-learning",
      "title": "Классическое Машинное Обучение",
      "cover_image_url": "...",
      "progress_percent": 35
    },
    ...
  ]
  ```

#### **2. Получение детальной программы курса с прогрессом**
* **Эндпоинт:** `GET /dashboard/courses/{slug}`
* **Назначение:** Запрос для страницы конкретного курса, получает программу с прогрессом по каждому уроку.
* **Аутентификация:** **Требуется**.
* **Request Body:** Нет.
* **Success Response (200 OK) (Схема `CourseDetailsWithProgress`):**
  ```json
  {
    "title": "Классическое Машинное Обучение",
    "overall_progress_percent": 35,
    "modules": [
      {
        "title": "Часть 1: Введение",
        "lessons": [
          { "lesson_id": "uuid-lesson-1", "slug": "what-is-ml", "title": "Урок 1: Что такое ML?", "status": "completed" },
          { "lesson_id": "uuid-lesson-2", "slug": "eda-tools", "title": "Урок 2: Инструментарий", "status": "in_progress" }
        ]
      },
      ...
    ]
  }
  ```

---

### **Ресурс: `Lessons` (Уроки)**
* **Роутер:** `/lessons`

#### **1. Получение контента урока**
* **Эндпоинт:** `GET /lessons/{lesson_id}`
* **Назначение:** Получить полное содержимое урока для отображения на странице.
* **Аутентификация:** **Требуется**.
* **Request Body:** Нет.
* **Success Response (200 OK) (Схема `LessonContent`):**
  ```json
  {
    "lesson_id": "uuid-lesson-1",
    "title": "Урок 1: Что такое ML?",
    "content_markdown": "### Введение \n Добро пожаловать...",
    "quiz": [
      {
        "question_id": "uuid-q-1",
        "question_text": "Какой тип обучения...",
        "answers": [
          { "answer_id": "uuid-a-1", "answer_text": "Supervised" },
          { "answer_id": "uuid-a-2", "answer_text": "Unsupervised" }
        ]
      }
    ]
  }
  ```

#### **2. Завершение урока**
* **Эндпоинт:** `POST /lessons/{lesson_id}/complete`
* **Назначение:** Отметить урок как пройденный для текущего пользователя.
* **Аутентификация:** **Требуется**.
* **Request Body:** Нет.
* **Success Response (200 OK):**
  ```json
  {
    "new_course_progress_percent": 38
  }
  ```

#### **3. Проверка ответа на квиз**
* **Эндпоинт:** `POST /quizzes/answers/check`
* **Назначение:** Проверить правильность ответа на вопрос квиза.
* **Аутентификация:** **Требуется**.
* **Request Body:**
  ```json
  {
    "question_id": "uuid-q-1",
    "selected_answer_id": "uuid-a-1"
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "is_correct": true,
    "correct_answer_id": "uuid-a-1"
  }
  ```
#### **4. Получение сырого контента урока (Админ)**
* **Эндпоинт:** `GET /lessons/{slug}/raw`
* **Назначение:** Получить сырой текст файла урока.
* **Аутентификация:** **Требуется (Админ)**.
* **Request Body:** Нет.
* **Success Response (200 OK):** Текст файла.

#### **5. Обновление сырого контента урока (Админ)**
* **Эндпоинт:** `PUT /lessons/{slug}/raw`
* **Назначение:** Обновить сырой текст файла урока.
* **Аутентификация:** **Требуется (Админ)**.
* **Request Body:** Текст файла.
* **Success Response (200 OK):**
  ```json
  {
    "message": "Lesson updated successfully"
  }
  ```
---

### **Ресурс: `Analytics` (Аналитика)**
* **Роутер:** `/activity-log`

#### **1. Отправка события активности**
* **Эндпоинт:** `POST /activity-log`
* **Назначение:** Зарегистрировать событие пользовательской активности (асинхронно).
* **Аутентификация:** **Требуется**.
* **Request Body (Схема `TrackEventRequest`):**
  ```json
  {
    "activity_type": "LESSON_COMPLETED",
    "details": {
      "lesson_slug": "python-syntax",
      "course_slug": "python-basics"
    }
  }
  ```
* **Success Response (202 Accepted):** Пустое тело ответа.

#### **2. Получение статистики активности пользователя**
* **Эндпоинт:** `GET /activity-log`
* **Назначение:** Получить агрегированную статистику активности пользователя за последний год.
* **Аутентификация:** **Требуется**.
* **Request Body:** Нет.
* **Success Response (200 OK) (Схема `ActivityDetailsResponse`):**
  ```json
  {
---

### **Ресурс: `Admin` (Администрирование)**
* **Роутер:** `/api/admin`

#### **1. Получение дерева контента**
* **Эндпоинт:** `GET /api/admin/content-tree`
* **Назначение:** Получить дерево структуры контента.
* **Аутентификация:** **Требуется (Админ)**.
* **Request Body:** Нет.
* **Success Response (200 OK) (Список схем ContentNode):**
  ```json
  [
    {
      "type": "course",
      "name": "course-slug",
      "path": "courses/course-slug",
      "children": [...],
      "configPath": "courses/course-slug/_course.yml"
    }
  ]
  ```

#### **2. Получение конфигурационного файла**
* **Эндпоинт:** `GET /api/admin/config-file?path=...`
* **Назначение:** Получить содержимое конфигурационного файла.
* **Аутентификация:** **Требуется (Админ)**.
* **Request Body:** Нет.
* **Success Response (200 OK):** Текст файла.

#### **3. Обновление конфигурационного файла**
* **Эндпоинт:** `PUT /api/admin/config-file?path=...`
* **Назначение:** Обновить содержимое конфигурационного файла.
* **Аутентификация:** **Требуется (Админ)**.
* **Request Body:** Текст файла.
* **Success Response (200 OK):**
  ```json
  {
    "status": "updated"
  }
  ```

#### **4. Создание элемента контента**
* **Эндпоинт:** `POST /api/admin/create/{item_type}`
* **Назначение:** Создать курс, модуль или урок.
* **Аутентификация:** **Требуется (Админ)**.
* **Request Body:** Зависит от item_type (CreateCourseRequest, etc.)
* **Success Response (201 Created):**
  ```json
  {
    "status": "created"
  }
  ```

#### **5. Удаление элемента контента**
* **Эндпоинт:** `DELETE /api/admin/item?path=...`
* **Назначение:** Удалить элемент контента.
* **Аутентификация:** **Требуется (Админ)**.
* **Request Body:** Нет.
* **Success Response (204 No Content):**

---
    "activities": [
      {
        "date": "2024-10-01",
        "LESSON_COMPLETED": 3,
        "QUIZ_ATTEMPT": 1
      },
      {
        "date": "2024-10-02",
        "LOGIN": 2,
        "CODE_EXECUTION": 5
      }
    ]
  }
  ```


---

### **Корневой эндпоинт**
* **Эндпоинт:** `GET /`
* **Назначение:** Проверка статуса API.
* **Аутентификация:** Не требуется.
* **Request Body:** Нет.
* **Success Response (200 OK):**
  ```json
  {
    "status": "ok"
  }
  ```

---

Эта структура эндпоинтов логически разделяет публичную и приватную части, четко определяет потоки данных и предоставляет фронтенду всю необходимую информацию для рендеринга страниц.