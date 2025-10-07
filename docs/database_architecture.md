
### **Структура Таблиц Базы Данных**

#### **Таблица 1: `profiles`**
*   **Назначение:** Хранит публичную информацию о пользователях, расширяя встроенную таблицу `auth.users`.
*   **Связь:** Один-к-одному с `auth.users`.

| Колонка | Тип | Описание |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**. Это **FOREIGN KEY**, ссылающийся на `auth.users.id`. Это ключ к успеху в Supabase. |
| `created_at` | `timestamptz` | Дата создания, `DEFAULT now()`. |
| `updated_at` | `timestamptz` | Дата обновления, `DEFAULT now()`. |
| `full_name` | `text` | Полное имя пользователя. |
| `avatar_url` | `text` | (Опционально) Ссылка на аватар пользователя. |
| `role` | `text` | Роль пользователя, по умолчанию 'student'. Может быть 'student' или 'admin'. |

*   **RLS Политики:**
    *   **`SELECT`:** Пользователь может видеть только свой собственный профиль (`auth.uid() = id`).
    *   **`UPDATE`:** Пользователь может обновлять только свой собственный профиль.

---

#### **Таблица 2: `courses`**
*   **Назначение:** Хранит информацию о курсах.

| Колонка | Тип | Описание |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**, `DEFAULT gen_random_uuid()`. |
| `created_at` | `timestamptz` | `DEFAULT now()`. |
| `title` | `text` | Название курса, `NOT NULL`. |
| `slug` | `text` | Уникальная строка для URL (напр., "classic-machine-learning"), `UNIQUE`. |
| `description` | `text` | Краткое описание курса. |
| `cover_image_url`| `text` | Ссылка на обложку курса. |

*   **RLS Политики:**
    *   **`SELECT`:** **Все** пользователи (включая анонимных) могут видеть список курсов. Это публичный каталог.
    *   **`INSERT`, `UPDATE`, `DELETE`:** Только для администраторов (потребуется отдельная логика ролей).

---

#### **Таблица 3: `modules` (Части курса)**
*   **Назначение:** Группирует уроки в логические блоки (Часть 1, Часть 2 и т.д.).

| Колонка | Тип | Описание |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**. |
| `created_at` | `timestamptz` | `DEFAULT now()`. |
| `course_id` | `uuid` | **FOREIGN KEY** на `courses.id`. |
| `title` | `text` | Название части (напр., "Фундаментальные Алгоритмы"). |
| `order_index` | `integer` | Порядок отображения (1, 2, 3...). |

*   **RLS Политики:**
    *   **`SELECT`:** Все могут видеть структуру модулей (это часть публичной программы курса).

---

#### **Таблица 4: `lessons`**
*   **Назначение:** Хранит контент одного урока.

| Колонка | Тип | Описание |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**. |
| `created_at` | `timestamptz` | `DEFAULT now()`. |
| `module_id` | `uuid` | **FOREIGN KEY** на `modules.id`. |
| `title` | `text` | Название урока. |
| `slug` | `text` | Уникальная строка для URL. |
| `content_markdown`| `text` | Основной теоретический материал урока. |
| `quiz_data` | `jsonb` | Структурированные данные квиза в формате JSON. |
| `order_index` | `integer` | Порядок урока внутри модуля. |

*   **RLS Политики:**
    *   **`SELECT`:** **Самая важная политика!** Пользователь может читать урок, **ТОЛЬКО ЕСЛИ** он записан на соответствующий курс. Это потребует `JOIN` в RLS-правиле.
    *   Пример RLS-правила для `SELECT`: `exists (select 1 from enrollments where enrollments.course_id = (select course_id from modules where modules.id = lessons.module_id) and enrollments.user_id = auth.uid())`

---

#### **Таблица 5: `enrollments` (Записи на курс)**
*   **Назначение:** Связующая таблица между пользователями и курсами.

| Колонка | Тип | Описание |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**. |
| `created_at` | `timestamptz` | `DEFAULT now()`. |
| `user_id` | `uuid` | **FOREIGN KEY** на `auth.users.id`. |
| `course_id` | `uuid` | **FOREIGN KEY** на `courses.id`. |

*   **RLS Политики:**
    *   **`SELECT`:** Пользователь может видеть только свои записи (`user_id = auth.uid()`).
    *   **`INSERT`:** Пользователь может создавать записи только для самого себя.

---

#### **Таблица 6: `user_lesson_progress`**
*   **Назначение:** Отслеживает статус прохождения каждого урока каждым пользователем.

| Колонка | Тип | Описание |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**. |
| `user_id` | `uuid` | **FOREIGN KEY** на `auth.users.id`. |
| `lesson_id` | `uuid` | **FOREIGN KEY** на `lessons.id`. |
| `status` | `text` | `DEFAULT 'not_started'`. Может быть `'in_progress'`, `'completed'`. |
| `completed_at` | `timestamptz` | Дата завершения. |

*   **RLS Политики:**
    *   **`SELECT`, `INSERT`, `UPDATE`:** Пользователь может работать только со своими записями о прогрессе (`user_id = auth.uid()`).

---

### **Автоматизация (Триггеры и Функции PostgreSQL)**

В редакторе SQL в Supabase можно добавить эти полезные функции.

1.  **Автоматическое обновление `updated_at`:**
    ```sql
    create extension if not exists moddatetime schema extensions;

    -- Создаем триггер для таблицы profiles
    create trigger handle_updated_at before update on profiles
    for each row execute procedure extensions.moddatetime (updated_at);
    ```
    *(Этот триггер нужно создать для каждой таблицы, где есть `updated_at`)*

2.  **Создание `slug` из `title`:**
    ```sql
    -- Функция для транслитерации и создания slug
    create or replace function public.slugify(text)
    returns text as $$
        -- ... (код функции для превращения "Привет, Мир!" в "privet-mir") ...
    $$ language sql immutable;

    -- Триггер, который будет вызывать эту функцию перед вставкой в courses
    create trigger slugify_course_title before insert on courses
    for each row execute procedure ...
    ```