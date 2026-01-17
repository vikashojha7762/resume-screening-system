# Authentication Examples

## Register a New User

### Request

```bash
curl -X POST "https://api.resumescreening.com/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T12:00:00Z"
}
```

## Login

### Request

```bash
curl -X POST "https://api.resumescreening.com/api/v1/auth/login/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePassword123!"
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiZXhwIjoxNzA0MTE2ODAwfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "token_type": "bearer"
}
```

## Get Current User

### Request

```bash
curl -X GET "https://api.resumescreening.com/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

## Python Example

```python
import requests

# Login
response = requests.post(
    "https://api.resumescreening.com/api/v1/auth/login/json",
    data={
        "username": "user@example.com",
        "password": "SecurePassword123!"
    }
)
token = response.json()["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
user_info = requests.get(
    "https://api.resumescreening.com/api/v1/auth/me",
    headers=headers
)
print(user_info.json())
```

## JavaScript Example

```javascript
// Login
const loginResponse = await fetch('https://api.resumescreening.com/api/v1/auth/login/json', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    username: 'user@example.com',
    password: 'SecurePassword123!'
  })
});

const { access_token } = await loginResponse.json();

// Use token for authenticated requests
const userResponse = await fetch('https://api.resumescreening.com/api/v1/auth/me', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

const user = await userResponse.json();
console.log(user);
```

## Error Responses

### Invalid Credentials

**Status:** 401 Unauthorized

```json
{
  "detail": "Incorrect email or password",
  "error_code": "AUTH_INVALID",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Token Expired

**Status:** 401 Unauthorized

```json
{
  "detail": "Token has expired",
  "error_code": "AUTH_EXPIRED",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

