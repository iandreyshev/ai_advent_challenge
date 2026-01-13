# Usage Examples

## Example 1: Getting Help About Authentication

```bash
$ python -m src.assistant.cli help "How does authentication work?"
```

**Response:**
```
Based on the API documentation (API.md), authentication works as follows:

**Login Endpoint**
POST /api/auth/login

The system uses JWT (JSON Web Token) based authentication:

1. Send credentials to /api/auth/login:
   {
     "email": "user@example.com",
     "password": "secure_password"
   }

2. Receive a JWT token in response:
   {
     "token": "jwt_token_here",
     "user": {...}
   }

3. Include token in subsequent requests:
   Authorization: Bearer {token}

**Current Git Context:**
Branch: main
Status: No uncommitted changes
```

## Example 2: Finding API Endpoints

```bash
$ python -m src.assistant.cli help "What API endpoints are available?"
```

**Response:**
```
According to the API documentation (docs/API.md), the following endpoints are available:

**Authentication:**
- POST /api/auth/login - User login
- POST /api/auth/register - User registration

**Users:**
- GET /api/users/:id - Get user information (requires auth)

**Projects:**
- GET /api/projects - List user's projects (with pagination)
- POST /api/projects - Create new project

All authenticated endpoints require the Authorization header:
Authorization: Bearer {token}

See docs/API.md for detailed request/response schemas.
```

## Example 3: Understanding Code Style

```bash
$ python -m src.assistant.cli help "What code style should I follow?"
```

**Response:**
```
Based on the Style Guide (docs/STYLE_GUIDE.md), follow these conventions:

**Naming:**
- Classes: PascalCase (e.g., UserManager)
- Functions/variables: snake_case (e.g., get_user_by_id)
- Constants: UPPER_SNAKE_CASE (e.g., MAX_RETRY_COUNT)

**Type Hints:**
All functions should have type hints:
```python
def get_user_by_id(user_id: str) -> User:
    pass
```

**Imports:**
Order: stdlib → third-party → local modules

**Docstrings:**
Use Google style format

See docs/STYLE_GUIDE.md for complete guidelines.
```

## Example 4: Database Schema Questions

```bash
$ python -m src.assistant.cli help "What's the database schema for users?"
```

**Response:**
```
From docs/DATABASE_SCHEMA.md:

**users table:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

**Relationships:**
- users (1) → (*) projects
- users (1) → (*) sessions

**Indexes:**
- idx_users_email
- idx_users_created_at
```

## Example 5: Searching Documentation

```bash
$ python -m src.assistant.cli search "error handling"
```

**Output:**
```
# Search Results for: error handling

## Result 1
Source: docs/API.md
Content: All errors are returned in format:
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  }
}

## Result 2
Source: docs/STYLE_GUIDE.md
Content: Use specific exceptions. Try-except with concrete exceptions.
Example:
try:
    result = process_document(doc)
except DocumentNotFoundError as e:
    logger.error(f"Document not found: {e}")
```

## Example 6: Finding Related Files

```bash
$ python -m src.assistant.cli files "authentication"
```

**Output:**
```
# Files related to: authentication

1. docs/API.md
2. docs/STYLE_GUIDE.md
3. docs/DATABASE_SCHEMA.md
```

## Example 7: Interactive Session

```bash
$ python -m src.assistant.cli interactive
```

**Session:**
```
┌─ Development Assistant ──────────────────────────┐
│                                                   │
│ Type your questions or commands:                 │
│   - Ask any question about the project           │
│   - Type 'quit' or 'exit' to leave              │
│   - Type 'git' to see git context               │
│                                                   │
└───────────────────────────────────────────────────┘

You: git

**Current Branch:** main
**Status:** 3 modified, 0 staged, 0 untracked

**Recent Commits:**
- e86a3f6: Задание дня 19
- bfd95db: Задание 18-го дня
- b4a869e: Доработал ридми

You: How do I handle errors in Python?