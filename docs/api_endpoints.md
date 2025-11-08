### **API v1 — Endpoint Design**

**Base URL:** `/api/v1`

---

### **Resource: `Auth` (Authentication)**
* **Router:** `/auth`

#### **1. Registration**
* **Endpoint:** `POST /auth/register`
* **Purpose:** Create a new user account.
* **Authentication:** Not required.
* **Request Body (Pydantic schema `UserCreate`):**
  ```json
  {
    "full_name": "Alexey Petrov",
    "email": "alexey.p@email.com",
    "password": "supersecretpassword123"
  }
  ```
* **Success Response (201 Created) (schema `Token`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

#### **2. Login (Token issued)**
* **Endpoint:** `POST /auth/login`
* **Purpose:** Authenticate a user and issue a JWT token.
* **Authentication:** Not required.
* **Request Body (OAuth2 form):** `username` (email) and `password`.
* **Success Response (200 OK) (schema `Token`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

#### **3. Refresh Tokens**
* **Endpoint:** `POST /auth/refresh`
* **Purpose:** Refresh JWT access tokens using a refresh token.
* **Authentication:** Not required (uses refresh token).
* **Request Body (schema `RefreshTokenRequest`):**
  ```json
  {
    "refresh_token": "refresh.jwt.token"
  }
  ```
* **Success Response (200 OK) (schema `RefreshTokenResponse`):**
  ```json
  {
    "access_token": "new.access.jwt.token",
    "refresh_token": "new.refresh.jwt.token",
    "token_type": "bearer",
    "expires_in": 900,
    "expires_at": 1640995200000
  }
  ```
* **Error Responses:**
  - `400 Bad Request`: Invalid refresh token format
  - `401 Unauthorized`: Invalid or expired refresh token
  - `429 Too Many Requests`: Rate limit exceeded
  - `500 Internal Server Error`: Token generation failed

#### **4. Get Own Profile**
* **Endpoint:** `GET /auth/me`
* **Purpose:** Retrieve information about the current authenticated user.
* **Authentication:** **Required (Bearer Token)**.
* **Request Body:** None.
* **Success Response (200 OK) (schema `User`):**
  ```json
  {
    "user_id": "uuid-goes-here",
    "full_name": "Alexey Petrov",
    "email": "alexey.p@email.com"
  }
  ```

#### **5. Check Email Existence**
* **Endpoint:** `POST /auth/check-email`
* **Purpose:** Verify whether an email is already registered.
* **Authentication:** Not required.
* **Request Body (schema `CheckEmailRequest`):**
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

#### **6. Forgot Password Request**
* **Endpoint:** `POST /auth/forgot-password`
* **Purpose:** Send a password reset email.
* **Authentication:** Not required.
* **Request Body (schema `ForgotPasswordRequest`):**
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

#### **7. Reset Password**
* **Endpoint:** `POST /auth/reset-password`
* **Purpose:** Reset the password using the recovery token.
* **Authentication:** Not required.
* **Request Body (schema `ResetPasswordRequest`):**
  ```json
  {
    "token": "recovery_token",
    "new_password": "newpassword123"
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "message": "Password updated successfully"
  }
  ```

---

### **Resource: `Courses`**
* **Router:** `/courses`

#### **1. List all courses (public catalogue)**
* **Endpoint:** `GET /courses`
* **Purpose:** Show every publicly available course on the platform.
* **Authentication:** Not required.
* **Request Body:** None.
* **Success Response (200 OK) (list of `CoursePublic` schema):**
  ```json
  [
    {
      "course_id": "uuid-course-1",
      "slug": "classic-machine-learning",
      "title": "Classic Machine Learning",
      "description": "Learn powerful algorithms...",
      "cover_image_url": "https://.../cover1.png"
    },
    ...
  ]
  ```

#### **2. Get course details (public page)**
* **Endpoint:** `GET /courses/{slug}`
* **Purpose:** Provide the detailed outline of a course for unauthenticated visitors.
* **Authentication:** Not required.
* **Request Body:** None.
* **Success Response (200 OK) (schema `CourseDetailsPublic`):**
  ```json
  {
    "course_id": "uuid-course-1",
    "slug": "classic-machine-learning",
    "title": "Classic Machine Learning",
    "description": "...",
    "cover_image_url": "...",
    "modules": [
      {
        "title": "Part 1: Introduction to the ML World",
        "lessons": [
          { "title": "Lesson 1: What is ML?" },
          { "title": "Lesson 2: Analyst Tooling" }
        ]
      },
      ...
    ]
  }
  ```

#### **3. Enroll in a course**
* **Endpoint:** `POST /courses/{slug}/enroll`
* **Purpose:** Enroll the current user into the selected course.
* **Authentication:** **Required**.
* **Request Body:** None.
* **Success Response (201 Created):** Empty body.

---

### **Resource: `Dashboard` (User Workspace)**
* **Router:** `/dashboard`

#### **1. List user courses**
* **Endpoint:** `GET /dashboard/my-courses`
* **Purpose:** Primary dashboard query that returns a list of the user’s courses with progress.
* **Authentication:** **Required**.
* **Request Body:** None.
* **Success Response (200 OK) (list of `CourseWithProgress` schema):**
  ```json
  [
    {
      "course_id": "uuid-course-1",
      "slug": "classic-machine-learning",
      "title": "Classic Machine Learning",
      "cover_image_url": "...",
      "progress_percent": 35
    },
    ...
  ]
  ```

#### **2. Get detailed course outline with progress**
* **Endpoint:** `GET /dashboard/courses/{slug}`
* **Purpose:** Fetch a course outline annotated with lesson progress for the authenticated user.
* **Authentication:** **Required**.
* **Request Body:** None.
* **Success Response (200 OK) (schema `CourseDetailsWithProgress`):**
  ```json
  {
    "title": "Classic Machine Learning",
    "overall_progress_percent": 35,
    "modules": [
      {
        "title": "Part 1: Introduction",
        "lessons": [
          { "lesson_id": "uuid-lesson-1", "slug": "what-is-ml", "title": "Lesson 1: What is ML?", "status": "completed" },
          { "lesson_id": "uuid-lesson-2", "slug": "eda-tools", "title": "Lesson 2: Tooling", "status": "in_progress" }
        ]
      },
      ...
    ]
  }
  ```

---

### **Resource: `Lessons`**
* **Router:** `/lessons`

#### **1. Fetch lesson content**
* **Endpoint:** `GET /lessons/{lesson_id}`
* **Purpose:** Retrieve the complete content for viewing a lesson.
* **Authentication:** **Required**.
* **Request Body:** None.
* **Success Response (200 OK) (schema `LessonContent`):**
  ```json
  {
    "lesson_id": "uuid-lesson-1",
    "title": "Lesson 1: What is ML?",
    "content_markdown": "### Introduction \n Welcome...",
    "quiz": [
      {
        "question_id": "uuid-q-1",
        "question_text": "Which learning type...",
        "answers": [
          { "answer_id": "uuid-a-1", "answer_text": "Supervised" },
          { "answer_id": "uuid-a-2", "answer_text": "Unsupervised" }
        ]
      }
    ]
  }
  ```

#### **2. Mark lesson as completed**
* **Endpoint:** `POST /lessons/{lesson_id}/complete`
* **Purpose:** Mark the lesson as completed for the current user.
* **Authentication:** **Required**.
* **Request Body:** None.
* **Success Response (200 OK):**
  ```json
  {
    "new_course_progress_percent": 38
  }
  ```

#### **3. Validate quiz answer**
* **Endpoint:** `POST /quizzes/answers/check`
* **Purpose:** Validate the provided quiz answer.
* **Authentication:** **Required**.
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

#### **4. Get raw lesson content (Admin)**
* **Endpoint:** `GET /lessons/{slug}/raw`
* **Purpose:** Retrieve the raw lesson file content.
* **Authentication:** **Required (Admin)**.
* **Request Body:** None.
* **Success Response (200 OK):** Raw file text.

#### **5. Update raw lesson content (Admin)**
* **Endpoint:** `PUT /lessons/{slug}/raw`
* **Purpose:** Update the raw lesson file content.
* **Authentication:** **Required (Admin)**.
* **Request Body:** Raw file text.
* **Success Response (200 OK):**
  ```json
  {
    "message": "Lesson updated successfully"
  }
  ```

---

### **Resource: `Analytics`**
* **Router:** `/activity-log`

#### **1. Track activity event**
* **Endpoint:** `POST /activity-log`
* **Purpose:** Record a user activity event asynchronously.
* **Authentication:** **Required**.
* **Request Body (schema `TrackEventRequest`):**
  ```json
  {
    "activity_type": "LESSON_COMPLETED",
    "details": {
      "lesson_slug": "python-syntax",
      "course_slug": "python-basics"
    }
  }
  ```
* **Success Response (202 Accepted):** Empty body.

#### **2. Get activity summary**
* **Endpoint:** `GET /activity-log`
* **Purpose:** Retrieve aggregated activity statistics for the last year.
* **Authentication:** **Required**.
* **Request Body:** None.
* **Success Response (200 OK) (schema `ActivityDetailsResponse`):**
  ```json
  {
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

### **Resource: `Admin`**
* **Router:** `/api/admin`

#### **1. Get content tree**
* **Endpoint:** `GET /api/admin/content-tree`
* **Purpose:** Retrieve the hierarchical structure of content elements.
* **Authentication:** **Required (Admin)**.
* **Request Body:** None.
* **Success Response (200 OK) (list of `ContentNode` schema):**
  ```json
  [
    {
      "type": "course",
      "name": "course-slug",
      "path": "courses/course-slug",
      "children": [...],
      "config_path": "courses/course-slug/_course.yml"
    }
  ]
  ```

#### **2. Get configuration file**
* **Endpoint:** `GET /api/admin/config-file?path=...`
* **Purpose:** Retrieve the contents of a configuration file.
* **Authentication:** **Required (Admin)**.
* **Request Body:** None.
* **Success Response (200 OK):** File content.

#### **3. Update configuration file**
* **Endpoint:** `PUT /api/admin/config-file?path=...`
* **Purpose:** Update the contents of a configuration file.
* **Authentication:** **Required (Admin)**.
* **Request Body:** File content.
* **Success Response (200 OK):**
  ```json
  {
    "status": "updated"
  }
  ```

#### **4. Create content item**
* **Endpoint:** `POST /api/admin/create/{item_type}`
* **Purpose:** Create a course, module, or lesson.
* **Authentication:** **Required (Admin)**.
* **Request Body:** Depends on `item_type` (e.g., `CreateCourseRequest`).
* **Success Response (201 Created):**
  ```json
  {
    "status": "created"
  }
  ```

#### **5. Delete content item**
* **Endpoint:** `DELETE /api/admin/item?path=...`
* **Purpose:** Delete a content element.
* **Authentication:** **Required (Admin)**.
* **Request Body:** None.
* **Success Response (204 No Content):**

---

### **Root Endpoint**
* **Endpoint:** `GET /`
* **Purpose:** Check API health.
* **Authentication:** Not required.
* **Request Body:** None.
* **Success Response (200 OK):**
  ```json
  {
    "status": "ok"
  }
  ```

---

This endpoint structure clearly separates public and private surfaces, defines data flows, and gives the frontend everything it needs to render pages.
