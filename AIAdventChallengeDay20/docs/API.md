# API Documentation

## REST API Endpoints

### Authentication

#### POST /api/auth/login
Аутентификация пользователя.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "token": "jwt_token_here",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

#### POST /api/auth/register
Регистрация нового пользователя.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "User Name"
}
```

### Users

#### GET /api/users/:id
Получить информацию о пользователе.

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "name": "User Name",
  "createdAt": "2025-01-13T10:00:00Z"
}
```

### Projects

#### GET /api/projects
Получить список проектов пользователя.

**Query Parameters:**
- `page` (optional): Номер страницы (default: 1)
- `limit` (optional): Количество на странице (default: 10)

**Response:**
```json
{
  "projects": [
    {
      "id": "project_id",
      "name": "Project Name",
      "description": "Description",
      "createdAt": "2025-01-13T10:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "pages": 5
}
```

#### POST /api/projects
Создать новый проект.

**Request:**
```json
{
  "name": "New Project",
  "description": "Project description"
}
```

## Error Handling

Все ошибки возвращаются в формате:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {}
  }
}
```

### Error Codes

- `AUTH_REQUIRED` (401): Требуется аутентификация
- `FORBIDDEN` (403): Недостаточно прав
- `NOT_FOUND` (404): Ресурс не найден
- `VALIDATION_ERROR` (400): Ошибка валидации данных
- `INTERNAL_ERROR` (500): Внутренняя ошибка сервера

## Rate Limiting

- 100 запросов в минуту для аутентифицированных пользователей
- 20 запросов в минуту для неаутентифицированных

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673616000
```
