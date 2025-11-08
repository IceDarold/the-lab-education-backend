### **Database Table Structure**

#### **Table 1: `profiles`**
* **Purpose:** Stores public profile metadata for users and extends `auth.users`.
* **Relationship:** One-to-one with `auth.users`.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY** and **FOREIGN KEY** referencing `auth.users.id`. This is the Supabase linkage key. |
| `created_at` | `timestamptz` | Creation timestamp, `DEFAULT now()`. |
| `updated_at` | `timestamptz` | Updated timestamp, `DEFAULT now()`. |
| `full_name` | `text` | User’s full name. |
| `avatar_url` | `text` | Optional link to the user’s avatar. |
| `role` | `text` | User role, defaults to `'student'`. Allowed values: `'student'`, `'admin'`. |

* **RLS Policies:**
  * **`SELECT`:** Users can only view their own profile (`auth.uid() = id`).
  * **`UPDATE`:** Users can only update their own profile.

---

#### **Table 2: `courses`**
* **Purpose:** Stores metadata for each course.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**, `DEFAULT gen_random_uuid()`. |
| `created_at` | `timestamptz` | `DEFAULT now()`. |
| `title` | `text` | Course title, `NOT NULL`. |
| `slug` | `text` | Unique slug for URLs (e.g., `"classic-machine-learning"`), `UNIQUE`. |
| `description` | `text` | Short summary of the course. |
| `cover_image_url` | `text` | Cover image URL. |

* **RLS Policies:**
  * **`SELECT`:** Public catalog—everyone (including anonymous users) may read.
  * **`INSERT`, `UPDATE`, `DELETE`:** Admin only (requires role-based logic).

---

#### **Table 3: `modules`**
* **Purpose:** Groups lessons into logical blocks (Part 1, Part 2, etc.).

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**. |
| `created_at` | `timestamptz` | `DEFAULT now()`. |
| `course_id` | `uuid` | **FOREIGN KEY** referencing `courses.id`. |
| `title` | `text` | Module title (e.g., “Core Algorithms”). |
| `order_index` | `integer` | Display order (1, 2, 3...). |

* **RLS Policies:**
  * **`SELECT`:** Public structure—anyone may read module outlines.

---

#### **Table 4: `lessons`**
* **Purpose:** Stores the content for each lesson.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**. |
| `created_at` | `timestamptz` | `DEFAULT now()`. |
| `module_id` | `uuid` | **FOREIGN KEY** referencing `modules.id`. |
| `title` | `text` | Lesson title. |
| `slug` | `text` | Unique slug used in URLs. |
| `content_markdown` | `text` | Primary lesson body in Markdown. |
| `quiz_data` | `jsonb` | Structured quiz metadata. |
| `order_index` | `integer` | Lesson order within the module. |

* **RLS Policies:**
  * **`SELECT`:** Users may read a lesson **only if** they are enrolled in the corresponding course. This requires a `JOIN` in the policy.
  * **Policy Example:** `exists (select 1 from enrollments where enrollments.course_id = (select course_id from modules where modules.id = lessons.module_id) and enrollments.user_id = auth.uid())`

---

#### **Table 5: `enrollments`**
* **Purpose:** Join table linking users to courses.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**. |
| `created_at` | `timestamptz` | `DEFAULT now()`. |
| `user_id` | `uuid` | **FOREIGN KEY** referencing `auth.users.id`. |
| `course_id` | `uuid` | **FOREIGN KEY** referencing `courses.id`. |

* **RLS Policies:**
  * **`SELECT`:** Users only see their own enrollments (`user_id = auth.uid()`).
  * **`INSERT`:** Users can only enroll themselves.

---

#### **Table 6: `user_lesson_progress`**
* **Purpose:** Tracks each user’s status on each lesson.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**. |
| `user_id` | `uuid` | **FOREIGN KEY** referencing `auth.users.id`. |
| `lesson_id` | `uuid` | **FOREIGN KEY** referencing `lessons.id`. |
| `status` | `text` | `DEFAULT 'not_started'`. Allowed values: `'not_started'`, `'in_progress'`, `'completed'`. |
| `completed_at` | `timestamptz` | Completion timestamp. |

* **RLS Policies:**
  * **`SELECT`, `INSERT`, `UPDATE`:** Users may only manipulate their own progress (`user_id = auth.uid()`).

---

#### **Table 7: `profiles` (duplicate explanation)**
* **Purpose:** Stores extended user metadata synchronized with `auth.users`.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY** referencing `auth.users.id`. |
| `created_at` | `timestamptz` | `DEFAULT now()`. |
| `updated_at` | `timestamptz` | `DEFAULT now()`. |
| `full_name` | `text` | User’s full name. |
| `avatar_url` | `text` | Optional avatar URL. |
| `role` | `text` | Defaults to `'student'`. |

* **RLS Policies:**
  * **`SELECT`:** Users see only their own profile.
  * **`UPDATE`:** Users update only their own profile.

---

#### **Table 8: `user_sessions`**
* **Purpose:** Tracks active sessions for refresh token management.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` | **PRIMARY KEY**. |
| `user_id` | `uuid` | **FOREIGN KEY** referencing `profiles.id`. |
| `refresh_token_hash` | `text` | Hashed refresh token for secure storage. |
| `device_info` | `text` | Optional device metadata. |
| `ip_address` | `text` | Optional IP address. |
| `expires_at` | `timestamptz` | Session expiration time. |
| `is_active` | `boolean` | Session flag, defaults to `true`. |
| `created_at` | `timestamptz` | `DEFAULT now()`. |
| `last_used_at` | `timestamptz` | Defaults to `now()`. |

* **Indexes:**
  * Index on `user_id` for fast lookup.
  * Unique index on `refresh_token_hash`.

* **RLS Policies:**
  * **`SELECT`, `INSERT`, `UPDATE`:** Reserved for system processes (not directly exposed to users).

---

### **Automation (Triggers and Functions)**

The Supabase SQL editor can host these helpers.

1. **Auto-update `updated_at`:**
   ```sql
   create extension if not exists moddatetime schema extensions;

   create trigger handle_updated_at before update on profiles
   for each row execute procedure extensions.moddatetime (updated_at);
   ```
   *(Repeat this trigger per table that has an `updated_at` column.)*

2. **Generate slug from title:**
   ```sql
   create or replace function public.slugify(text)
   returns text as $$
       -- ... (function body that converts "Привет, Мир!" into "privet-mir") ...
   $$ language sql immutable;

   create trigger slugify_course_title before insert on courses
   for each row execute procedure ...
   ```
