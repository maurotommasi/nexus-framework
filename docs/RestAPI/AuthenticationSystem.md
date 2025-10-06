# Authentication Service Documentation

## Overview

This document provides comprehensive documentation for the `AuthenticationService` class and all authentication endpoints in the SaaS platform.

## Table of Contents

1. [Setup & Configuration](#setup--configuration)
2. [Class Methods Reference](#class-methods-reference)
3. [API Endpoints Reference](#api-endpoints-reference)
4. [Database Schema Considerations](#database-schema-considerations)
5. [Security Best Practices](#security-best-practices)

---

## Setup & Configuration

### Environment Variables

```bash
# JWT Configuration
SECRET_KEY="your-secret-key-min-32-chars"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/saas_db"

# Redis
REDIS_URL="redis://localhost:6379"

# Email (SMTP)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
FROM_EMAIL="noreply@yoursaas.com"

# SSO Providers
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
GITHUB_CLIENT_ID="your-github-client-id"
GITHUB_CLIENT_SECRET="your-github-client-secret"

# Security
PASSWORD_MIN_LENGTH=8
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
```

### Installation

```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] \
    python-multipart aiosmtplib asyncpg redis pyotp qrcode httpx
```

### Initialize Service

```python
from auth_service import AuthenticationService, app

# Create service instance
auth_service = AuthenticationService()

# Initialize (call on startup)
await auth_service.initialize()

# Close connections (call on shutdown)
await auth_service.close()
```

---

## Class Methods Reference

### Core Initialization

#### `initialize()`
**Purpose**: Initialize database and Redis connections

**Input**: None

**Output**: None

**Usage**:
```python
await auth_service.initialize()
```

**Notes**: Must be called before using any other methods

---

#### `close()`
**Purpose**: Close all database and Redis connections

**Input**: None

**Output**: None

**Usage**:
```python
await auth_service.close()
```

---

### Database Helper Methods

#### `get_table_name(base_table: str, user_tier: str, user_id: str = None) -> str`
**Purpose**: Get appropriate table name based on user tier

**Input**:
- `base_table` (str): Base table name (e.g., "users", "pods")
- `user_tier` (str): User tier ("free", "normal", "pro", "enterprise")
- `user_id` (str, optional): User ID for free/normal tier table prefixing

**Output**: 
- (str): Formatted table name

**Example**:
```python
# Free/Normal tier
table_name = auth_service.get_table_name("data", "free", "user-123")
# Returns: "nexus_user-123_data"

# Pro/Enterprise tier
table_name = auth_service.get_table_name("data", "pro")
# Returns: "data"
```

**Notes**: 
- Free/Normal users share tables with prefix `nexus_{user_id}_{table}`
- Pro/Enterprise users have dedicated databases

---

#### `get_db_connection(user_tier: str)`
**Purpose**: Get database connection based on user tier

**Input**:
- `user_tier` (str): User tier

**Output**: 
- Database connection object

**Usage**:
```python
conn = await auth_service.get_db_connection("free")
try:
    # Use connection
    result = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
finally:
    await auth_service.db_pool.release(conn)
```

---

### Password Management

#### `hash_password(password: str) -> str`
**Purpose**: Hash a password using bcrypt

**Input**:
- `password` (str): Plain text password

**Output**: 
- (str): Hashed password

**Example**:
```python
hashed = auth_service.hash_password("MySecureP@ss123")
# Returns: "$2b$12$..."
```

---

#### `verify_password(plain_password: str, hashed_password: str) -> bool`
**Purpose**: Verify password against hash

**Input**:
- `plain_password` (str): Plain text password
- `hashed_password` (str): Bcrypt hash

**Output**: 
- (bool): True if password matches

**Example**:
```python
is_valid = auth_service.verify_password("MySecureP@ss123", hashed)
# Returns: True or False
```

---

### JWT Token Management

#### `create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str`
**Purpose**: Create JWT access token

**Input**:
- `data` (dict): Token payload (should include "sub" for user_id)
- `expires_delta` (timedelta, optional): Custom expiration time

**Output**: 
- (str): JWT token

**Example**:
```python
token = auth_service.create_access_token(
    data={"sub": "user-123", "email": "user@example.com", "tier": "free"}
)
# Returns: "eyJhbGciOiJIUzI1NiIs..."
```

---

#### `create_refresh_token(data: dict) -> str`
**Purpose**: Create JWT refresh token

**Input**:
- `data` (dict): Token payload

**Output**: 
- (str): JWT refresh token

**Example**:
```python
refresh = auth_service.create_refresh_token(data={"sub": "user-123"})
```

---

#### `verify_token(token: str) -> Dict[str, Any]`
**Purpose**: Verify and decode JWT token

**Input**:
- `token` (str): JWT token

**Output**: 
- (dict): Decoded token payload

**Raises**:
- `HTTPException(401)`: Invalid or expired token

**Example**:
```python
try:
    payload = await auth_service.verify_token(token)
    user_id = payload['sub']
except HTTPException:
    print("Invalid token")
```

---

#### `blacklist_token(token: str, expires_in: int)`
**Purpose**: Add token to blacklist (for logout)

**Input**:
- `token` (str): JWT token to blacklist
- `expires_in` (int): Seconds until token naturally expires

**Output**: None

**Example**:
```python
await auth_service.blacklist_token(token, 1800)  # 30 minutes
```

---

### User Registration & Authentication

#### `register_user(email: str, password: str, first_name: str, last_name: str, phone: Optional[str] = None) -> Dict[str, Any]`
**Purpose**: Register a new user

**Input**:
- `email` (str): User email
- `password` (str): Password (will be hashed)
- `first_name` (str): First name
- `last_name` (str): Last name
- `phone` (str, optional): Phone number

**Output**: 
```python
{
    "user_id": "uuid",
    "email": "user@example.com",
    "message": "User registered successfully. Please verify your email.",
    "verification_required": True
}
```

**Raises**:
- `HTTPException(400)`: Email already registered

**Example**:
```python
result = await auth_service.register_user(
    email="newuser@example.com",
    password="SecurePass123!",
    first_name="John",
    last_name="Doe",
    phone="+1234567890"
)
```

---

#### `login_user(email: str, password: str, ip_address: str, user_agent: str) -> Dict[str, Any]`
**Purpose**: Login user with email/password

**Input**:
- `email` (str): User email
- `password` (str): Password
- `ip_address` (str): Client IP address
- `user_agent` (str): User agent string

**Output** (if 2FA disabled):
```python
{
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 1800  # seconds
}
```

**Output** (if 2FA enabled):
```python
{
    "requires_2fa": True,
    "session_token": "temp_session_token_for_2fa"
}
```

**Raises**:
- `HTTPException(401)`: Invalid credentials
- `HTTPException(403)`: Account suspended or email not verified
- `HTTPException(429)`: Too many login attempts

**Example**:
```python
result = await auth_service.login_user(
    email="user@example.com",
    password="SecurePass123!",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)

if result.get("requires_2fa"):
    # Prompt for 2FA code
    pass
else:
    # Login successful
    access_token = result["access_token"]
```

---

#### `logout_user(token: str, user_id: str)`
**Purpose**: Logout user and invalidate token

**Input**:
- `token` (str): Access token to invalidate
- `user_id` (str): User ID

**Output**: None

**Example**:
```python
await auth_service.logout_user(access_token, "user-123")
```

---

### Email Verification

#### `verify_email(token: str) -> bool`
**Purpose**: Verify user email with token

**Input**:
- `token` (str): Email verification token

**Output**: 
- (bool): True if successful

**Raises**:
- `HTTPException(400)`: Invalid, used, or expired token

**Example**:
```python
try:
    await auth_service.verify_email(token)
    print("Email verified!")
except HTTPException as e:
    print(f"Verification failed: {e.detail}")
```

---

#### `resend_verification_email(email: str)`
**Purpose**: Resend verification email

**Input**:
- `email` (str): User email

**Output**: None

**Raises**:
- `HTTPException(404)`: User not found
- `HTTPException(400)`: Email already verified

**Example**:
```python
await auth_service.resend_verification_email("user@example.com")
```

---

### Password Reset

#### `request_password_reset(email: str)`
**Purpose**: Request password reset

**Input**:
- `email` (str): User email

**Output**: None (silent if email doesn't exist for security)

**Example**:
```python
await auth_service.request_password_reset("user@example.com")
```

---

#### `reset_password(token: str, new_password: str)`
**Purpose**: Reset password with token

**Input**:
- `token` (str): Password reset token
- `new_password` (str): New password

**Output**: None

**Raises**:
- `HTTPException(400)`: Invalid, used, or expired token

**Example**:
```python
await auth_service.reset_password(
    token="reset_token_123",
    new_password="NewSecurePass456!"
)
```

**Notes**: Invalidates all user sessions for security

---

#### `change_password(user_id: str, old_password: str, new_password: str)`
**Purpose**: Change password (when logged in)

**Input**:
- `user_id` (str): User ID
- `old_password` (str): Current password
- `new_password` (str): New password

**Output**: None

**Raises**:
- `HTTPException(400)`: Incorrect current password

**Example**:
```python
await auth_service.change_password(
    user_id="user-123",
    old_password="OldPass123",
    new_password="NewPass456!"
)
```

---

### Two-Factor Authentication (2FA)

#### `enable_2fa(user_id: str, password: str) -> Dict[str, Any]`
**Purpose**: Enable 2FA for user

**Input**:
- `user_id` (str): User ID
- `password` (str): User password (for verification)

**Output**:
```python
{
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_code": "data:image/png;base64,iVBORw0KGgo...",
    "backup_codes": ["abcd1234", "efgh5678", ...]
}
```

**Raises**:
- `HTTPException(400)`: Incorrect password or 2FA already enabled

**Example**:
```python
result = await auth_service.enable_2fa("user-123", "UserPassword123")
qr_code = result["qr_code"]  # Display to user
backup_codes = result["backup_codes"]  # User must save these
```

**Important**: User must save backup codes securely!

---

#### `verify_2fa(session_token: str, code: str, ip_address: str, user_agent: str) -> Dict[str, Any]`
**Purpose**: Verify 2FA code and complete login

**Input**:
- `session_token` (str): Temporary session token from login
- `code` (str): 6-digit TOTP code or backup code
- `ip_address` (str): Client IP
- `user_agent` (str): User agent

**Output**:
```python
{
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

**Raises**:
- `HTTPException(400)`: Invalid code or session

**Example**:
```python
tokens = await auth_service.verify_2fa(
    session_token="temp_token_123",
    code="123456",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)
```

---

#### `disable_2fa(user_id: str, password: str, code: str)`
**Purpose**: Disable 2FA

**Input**:
- `user_id` (str): User ID
- `password` (str): User password
- `code` (str): Current 2FA code

**Output**: None

**Raises**:
- `HTTPException(400)`: Incorrect password/code or 2FA not enabled

**Example**:
```python
await auth_service.disable_2fa(
    user_id="user-123",
    password="UserPassword123",
    code="123456"
)
```

---

#### `send_2fa_email(session_token: str, email: str)`
**Purpose**: Send 2FA code via email (alternative to TOTP)

**Input**:
- `session_token` (str): Temporary session token
- `email` (str): User email

**Output**:
```python
{
    "sent": True,
    "expires_in": 300  # seconds
}
```

**Example**:
```python
result = await auth_service.send_2fa_email(
    session_token="temp_token",
    email="user@example.com"
)
```

---

#### `regenerate_backup_codes(user_id: str) -> List[str]`
**Purpose**: Regenerate 2FA backup codes

**Input**:
- `user_id` (str): User ID

**Output**: 
- (List[str]): New backup codes

**Example**:
```python
new_codes = await auth_service.regenerate_backup_codes("user-123")
# Returns: ["code1", "code2", ..., "code10"]
```

---

### Single Sign-On (SSO)

#### `initiate_sso(provider: str, redirect_uri: str) -> Dict[str, str]`
**Purpose**: Initiate SSO flow

**Input**:
- `provider` (str): SSO provider ("google", "github", "azure", "okta")
- `redirect_uri` (str): Callback URL

**Output**:
```python
{
    "authorization_url": "https://accounts.google.com/o/oauth2/...",
    "state": "random_state_token"
}
```

**Raises**:
- `HTTPException(400)`: Unsupported provider

**Example**:
```python
result = await auth_service.initiate_sso(
    provider="google",
    redirect_uri="https://yoursaas.com/auth/callback"
)
# Redirect user to result["authorization_url"]
```

---

#### `handle_sso_callback(code: str, state: str, ip_address: str, user_agent: str) -> Dict[str, Any]`
**Purpose**: Handle SSO callback and login/register user

**Input**:
- `code` (str): Authorization code from provider
- `state` (str): State token for CSRF protection
- `ip_address` (str): Client IP
- `user_agent` (str): User agent

**Output**:
```python
{
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

**Raises**:
- `HTTPException(400)`: Invalid state
- `HTTPException(403)`: Account suspended

**Example**:
```python
# In callback endpoint
tokens = await auth_service.handle_sso_callback(
    code=request.args.get("code"),
    state=request.args.get("state"),
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

**Notes**: 
- Automatically creates user if doesn't exist
- Links SSO provider to existing email if found

---

#### `link_sso_provider(user_id: str, provider: str, provider_user_id: str)`
**Purpose**: Link SSO provider to existing account

**Input**:
- `user_id` (str): User ID
- `provider` (str): Provider name
- `provider_user_id` (str): Provider's user ID

**Output**: None

---

#### `unlink_sso_provider(user_id: str)`
**Purpose**: Unlink SSO provider from account

**Input**:
- `user_id` (str): User ID

**Output**: None

**Raises**:
- `HTTPException(400)`: Cannot unlink if no password set

**Example**:
```python
try:
    await auth_service.unlink_sso_provider("user-123")
except HTTPException:
    print("Set a password before unlinking SSO")
```

---

### Session Management

#### `create_session(user_id: str, access_token: str, refresh_token: str, ip_address: str, user_agent: str) -> str`
**Purpose**: Create user session

**Input**:
- `user_id` (str): User ID
- `access_token` (str): Access token
- `refresh_token` (str): Refresh token
- `ip_address` (str): Client IP
- `user_agent` (str): User agent

**Output**: 
- (str): Session ID

---

#### `get_user_sessions(user_id: str) -> List[Dict[str, Any]]`
**Purpose**: Get all active sessions for user

**Input**:
- `user_id` (str): User ID

**Output**:
```python
[
    {
        "id": "session-uuid",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
        "created_at": "2025-01-01T00:00:00",
        "last_activity_at": "2025-01-01T12:00:00"
    },
    ...
]
```

---

#### `revoke_session(session_id: str, user_id: str)`
**Purpose**: Revoke specific session

**Input**:
- `session_id` (str): Session ID
- `user_id` (str): User ID

**Output**: None

---

#### `revoke_all_sessions(user_id: str, except_token: str = None)`
**Purpose**: Revoke all sessions except current

**Input**:
- `user_id` (str): User ID
- `except_token` (str, optional): Token to keep active

**Output**: None

**Example**:
```python
# Revoke all other sessions
await auth_service.revoke_all_sessions("user-123", current_token)
```

---

#### `refresh_access_token(refresh_token: str) -> Dict[str, Any]`
**Purpose**: Refresh access token

**Input**:
- `refresh_token` (str): Refresh token

**Output**:
```python
{
    "access_token": "new_access_token",
    "token_type": "bearer",
    "expires_in": 1800
}
```

**Raises**:
- `HTTPException(400)`: Invalid token type
- `HTTPException(401)`: Invalid or expired token

---

### API Key Management

#### `create_api_key(user_id: str, organization_id: str, name: str, scopes: List[str], expires_at: Optional[datetime] = None) -> Dict[str, str]`
**Purpose**: Create API key

**Input**:
- `user_id` (str): User ID
- `organization_id` (str): Organization ID
- `name` (str): Key name/description
- `scopes` (List[str]): Permission scopes
- `expires_at` (datetime, optional): Expiration date

**Output**:
```python
{
    "id": "key-uuid",
    "key": "sk_live_abc123...",  # Only shown once!
    "prefix": "sk_live_abc1"
}
```

**Example**:
```python
api_key = await auth_service.create_api_key(
    user_id="user-123",
    organization_id="org-456",
    name="Production API Key",
    scopes=["read:pods", "write:pods"],
    expires_at=datetime.utcnow() + timedelta(days=365)
)
# IMPORTANT: Save api_key["key"] - it won't be shown again!
```

---

#### `list_api_keys(user_id: str, organization_id: str) -> List[Dict[str, Any]]`
**Purpose**: List user's API keys

**Input**:
- `user_id` (str): User ID
- `organization_id` (str): Organization ID

**Output**:
```python
[
    {
        "id": "key-uuid",
        "name": "Production Key",
        "key_prefix": "sk_live_abc1",
        "scopes": ["read:pods"],
        "created_at": "2025-01-01T00:00:00",
        "expires_at": "2026-01-01T00:00:00",
        "last_used_at": "2025-01-15T10:30:00",
        "is_active": True
    },
    ...
]
```

---

#### `revoke_api_key(key_id: str, user_id: str)`
**Purpose**: Revoke API key

**Input**:
- `key_id` (str): API key ID
- `user_id` (str): User ID

**Output**: None

---

#### `verify_api_key(api_key: str) -> Dict[str, Any]`
**Purpose**: Verify API key and return associated data

**Input**:
- `api_key` (str): API key string

**Output**:
```python
{
    "user_id": "user-123",
    "organization_id": "org-456",
    "scopes": ["read:pods", "write:pods"]
}
```

**Raises**:
- `HTTPException(401)`: Invalid, revoked, or expired key

**Example**:
```python
try:
    key_data = await auth_service.verify_api_key(api_key)
    if "write:pods" in key_data["scopes"]:
        # Allow operation
        pass
except HTTPException:
    # Invalid key
    pass
```

---

## API Endpoints Reference

### Base URL
```
http://localhost:8001/api/v1/auth
```

### Authentication Endpoints

#### POST `/register`
Register new user

**Request**:
```json
{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890"
}
```

**Response** (201):
```json
{
    "user_id": "uuid",
    "email": "user@example.com",
    "message": "User registered successfully. Please verify your email.",
    "verification_required": true
}
```

---

#### POST `/login`
Login with email/password

**Request**:
```
Form Data:
  username: user@example.com
  password: SecurePass123!
```

**Response** (200):
```json
{
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

**Or** (if 2FA enabled):
```json
{
    "requires_2fa": true,
    "session_token": "temp_session_token"
}
```

---

#### POST `/logout`
Logout user

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200):
```json
{
    "message": "Logged out successfully"
}
```

---

#### POST `/refresh`
Refresh access token

**Request**:
```json
{
    "refresh_token": "eyJhbGci..."
}
```

**Response** (200):
```json
{
    "access_token": "new_token",
    "token_type": "bearer",
    "expires_in": 1800
}
```

---

#### POST `/verify-email?token={token}`
Verify email address

**Response** (200):
```json
{
    "message": "Email verified successfully"
}
```

---

#### POST `/resend-verification`
Resend verification email

**Request**:
```json
{
    "email": "user@example.com"
}
```

**Response** (200):
```json
{
    "message": "Verification email sent"
}
```

---

#### POST `/password/reset-request`
Request password reset

**Request**:
```json
{
    "email": "user@example.com"
}
```

**Response** (200):
```json
{
    "message": "If that email exists, reset instructions have been sent"
}
```

---

#### POST `/password/reset`
Reset password with token

**Request**:
```json
{
    "token": "reset_token",
    "new_password": "NewSecurePass456!"
}
```

**Response** (200):
```json
{
    "message": "Password reset successfully"
}
```

---

#### POST `/password/change`
Change password (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request**:
```json
{
    "old_password": "OldPass123",
    "new_password": "NewPass456!"
}
```

**Response** (200):
```json
{
    "message": "Password changed successfully"
}
```

---

### SSO Endpoints

#### POST `/sso/initiate`
Initiate SSO flow

**Request**:
```json
{
    "provider": "google",
    "redirect_uri": "https://yoursaas.com/auth/callback"
}
```

**Response** (200):
```json
{
    "authorization_url": "https://accounts.google.com/o/oauth2/...",
    "state": "random_state_token"
}
```

---

#### POST `/sso/callback`
Handle SSO callback

**Request**:
```json
{
    "code": "authorization_code_from_provider",
    "state": "state_token"
}
```

**Response** (200):
```json
{
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

---

#### GET `/sso/providers`
List available SSO providers

**Response** (200):
```json
{
    "providers": ["google", "github", "azure", "okta"]
}
```

---

#### DELETE `/sso/unlink`
Unlink SSO provider (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200):
```json
{
    "message": "SSO provider unlinked"
}
```

---

### 2FA Endpoints

#### POST `/2fa/enable`
Enable 2FA (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request**:
```json
{
    "password": "UserPassword123"
}
```

**Response** (200):
```json
{
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_code": "data:image/png;base64,iVBORw0KGgo...",
    "backup_codes": [
        "abcd1234",
        "efgh5678",
        "ijkl9012",
        "mnop3456",
        "qrst7890"
    ]
}
```

---

#### POST `/2fa/verify`
Verify 2FA code

**Request**:
```json
{
    "session_token": "temp_session_token",
    "code": "123456"
}
```

**Response** (200):
```json
{
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

---

#### POST `/2fa/disable`
Disable 2FA (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request**:
```json
{
    "password": "UserPassword123",
    "code": "123456"
}
```

**Response** (200):
```json
{
    "message": "2FA disabled successfully"
}
```

---

#### POST `/2fa/send-code?session_token={token}`
Send 2FA code via email

**Response** (200):
```json
{
    "sent": true,
    "expires_in": 300
}
```

---

#### POST `/2fa/regenerate-backup-codes`
Regenerate backup codes (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200):
```json
{
    "backup_codes": [
        "new1234",
        "new5678",
        "..."
    ]
}
```

---

### Session Management Endpoints

#### GET `/sessions`
List all active sessions (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200):
```json
{
    "sessions": [
        {
            "id": "session-uuid",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0 ...",
            "created_at": "2025-01-01T00:00:00Z",
            "last_activity": "2025-01-01T12:00:00Z",
            "is_current": true
        }
    ]
}
```

---

#### DELETE `/sessions/{session_id}`
Revoke specific session (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200):
```json
{
    "message": "Session revoked"
}
```

---

#### DELETE `/sessions`
Revoke all other sessions (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200):
```json
{
    "message": "All other sessions revoked"
}
```

---

### API Key Management Endpoints

#### POST `/api-keys`
Create API key (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request**:
```json
{
    "name": "Production API Key",
    "scopes": ["read:pods", "write:pods", "read:modules"],
    "expires_at": "2026-01-01T00:00:00Z"
}
```

**Response** (200):
```json
{
    "id": "key-uuid",
    "key": "sk_live_abc123xyz789...",
    "prefix": "sk_live_abc1"
}
```

**⚠️ IMPORTANT**: The full key is only shown once! Save it securely.

---

#### GET `/api-keys`
List API keys (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200):
```json
{
    "api_keys": [
        {
            "id": "key-uuid",
            "name": "Production API Key",
            "key_prefix": "sk_live_abc1",
            "scopes": ["read:pods", "write:pods"],
            "created_at": "2025-01-01T00:00:00Z",
            "expires_at": "2026-01-01T00:00:00Z",
            "last_used_at": "2025-01-15T10:30:00Z",
            "is_active": true
        }
    ]
}
```

---

#### DELETE `/api-keys/{key_id}`
Revoke API key (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200):
```json
{
    "message": "API key revoked"
}
```

---

#### GET `/verify`
Verify current token (requires auth)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200):
```json
{
    "valid": true,
    "user": {
        "sub": "user-uuid",
        "email": "user@example.com",
        "tier": "free",
        "exp": 1704110400
    }
}
```

---

#### GET `/health`
Health check endpoint

**Response** (200):
```json
{
    "status": "healthy",
    "service": "authentication"
}
```

---

## Database Schema Considerations

### Table Naming Strategy

For **Free/Normal Tier** users:
```
Original table: users
Shared table: users (main user table)

Original table: user_data
Prefixed table: nexus_{user_id}_user_data
```

For **Pro/Enterprise Tier** users:
```
All tables use standard names without prefixes
Database is dedicated per organization
```

### Required Indexes for Performance

```sql
-- Critical indexes for authentication
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_sso ON users(sso_provider, sso_provider_id);
CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(token);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_verification_token ON email_verification_tokens(token);
CREATE INDEX idx_reset_token ON password_reset_tokens(token);
```

### Redis Keys Structure

```
# Session tokens
2fa_session:{session_token} -> user_id (TTL: 10 minutes)

# 2FA email codes
2fa_email_code:{session_token} -> code (TTL: 5 minutes)

# SSO state
sso_state:{state} -> provider (TTL: 10 minutes)

# Blacklisted tokens
blacklist:{token} -> "1" (TTL: token expiration time)

# Login attempts
login_attempts:{email} -> count (TTL: 15 minutes)
```

---

## Security Best Practices

### 1. Password Requirements

Passwords must meet these criteria:
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 digit
- At least 1 special character (recommended)

```python
@validator('password')
def validate_password(cls, v):
    if len(v) < 8:
        raise ValueError('Password must be at least 8 characters')
    if not any(char.isdigit() for char in v):
        raise ValueError('Password must contain at least one digit')
    if not any(char.isupper() for char in v):
        raise ValueError('Password must contain at least one uppercase letter')
    return v
```

### 2. Rate Limiting

Implement rate limiting to prevent brute force attacks:

```python
# Login attempts: 5 per 15 minutes per email
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# API calls: Based on tier
FREE_TIER_RATE_LIMIT = 100  # requests per minute
NORMAL_TIER_RATE_LIMIT = 1000
PRO_TIER_RATE_LIMIT = 5000
ENTERPRISE_TIER_RATE_LIMIT = None  # Unlimited
```

### 3. Token Security

**Access Tokens**:
- Short-lived (30 minutes)
- Stored in memory (not localStorage)
- Transmitted via Authorization header only

**Refresh Tokens**:
- Longer-lived (7 days)
- Stored in httpOnly secure cookie
- Can be revoked

**API Keys**:
- Prefixed (sk_live_ or sk_test_)
- Hashed in database (SHA256)
- Supports scopes and expiration

### 4. 2FA Implementation

**TOTP (Time-based One-Time Password)**:
- Uses industry-standard TOTP (RFC 6238)
- 30-second time window
- 6-digit codes
- Backup codes for recovery

**Email 2FA**:
- Alternative for users without authenticator app
- 6-digit code
- 5-minute expiration
- Stored in Redis

### 5. Session Management

**Best Practices**:
- Track IP and User-Agent
- Allow users to view active sessions
- Provide logout from all devices
- Automatic session cleanup

```python
# Cleanup expired sessions (run daily)
DELETE FROM user_sessions 
WHERE expires_at < NOW();
```

### 6. SSO Security

**State Parameter**:
- Prevents CSRF attacks
- Random 32-byte token
- 10-minute expiration
- Single use only

**Provider Validation**:
- Verify state before processing callback
- Validate tokens with provider
- Store provider-specific user ID

### 7. API Key Security

**Generation**:
```python
api_key = f"sk_{'test' if DEBUG else 'live'}_{secrets.token_urlsafe(32)}"
```

**Storage**:
- Store SHA256 hash only
- Keep first 12 chars as prefix for identification
- Never log full key

**Verification**:
```python
key_hash = hashlib.sha256(api_key.encode()).hexdigest()
# Compare hash, not plain key
```

### 8. Email Security

**Verification Tokens**:
- 32-byte random token
- 24-hour expiration
- Single use only
- Marked as used after verification

**Password Reset**:
- 32-byte random token
- 1-hour expiration
- Invalidates all sessions after reset

### 9. Audit Logging

Log all security-relevant events:

```python
# Events to log
- Login attempts (success/failure)
- Password changes/resets
- 2FA enable/disable
- SSO link/unlink
- API key creation/revocation
- Session revocations
```

### 10. Data Protection

**Encryption**:
- Passwords: bcrypt with cost factor 12
- Tokens: URL-safe random bytes
- 2FA secrets: Encrypted at rest
- Backup codes: Hashed (bcrypt)

**Database**:
- Use prepared statements (SQL injection protection)
- Encrypt sensitive columns
- Regular backups
- Point-in-time recovery

---

## Usage Examples

### Complete User Registration Flow

```python
from auth_service import AuthenticationService

auth_service = AuthenticationService()
await auth_service.initialize()

# 1. Register user
result = await auth_service.register_user(
    email="newuser@example.com",
    password="SecurePass123!",
    first_name="John",
    last_name="Doe"
)
# User receives verification email

# 2. User clicks link in email
await auth_service.verify_email(token_from_email)
# Email is now verified

# 3. User can now login
login_result = await auth_service.login_user(
    email="newuser@example.com",
    password="SecurePass123!",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)

# 4. Store tokens
access_token = login_result["access_token"]
refresh_token = login_result["refresh_token"]
```

### Implementing 2FA

```python
# 1. User enables 2FA
setup = await auth_service.enable_2fa(
    user_id="user-123",
    password="SecurePass123!"
)

# 2. Display QR code to user
qr_code = setup["qr_code"]  # Base64 PNG
backup_codes = setup["backup_codes"]  # Save these!

# 3. User scans QR code with authenticator app

# 4. On next login
login_result = await auth_service.login_user(...)
if login_result.get("requires_2fa"):
    session_token = login_result["session_token"]
    
    # 5. Prompt user for 2FA code
    # User enters code from authenticator app
    
    # 6. Verify code
    tokens = await auth_service.verify_2fa(
        session_token=session_token,
        code="123456",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0..."
    )
    
    access_token = tokens["access_token"]
```

### Using SSO

```python
# 1. Initiate SSO flow
sso_data = await auth_service.initiate_sso(
    provider="google",
    redirect_uri="https://yoursaas.com/auth/callback"
)

# 2. Redirect user to authorization URL
# User authorizes on Google's site

# 3. Handle callback
tokens = await auth_service.handle_sso_callback(
    code=request.args.get("code"),
    state=request.args.get("state"),
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)

# User is now logged in or account created
access_token = tokens["access_token"]
```

### Managing API Keys

```python
# 1. Create API key
api_key_data = await auth_service.create_api_key(
    user_id="user-123",
    organization_id="org-456",
    name="Production API Key",
    scopes=["read:pods", "write:pods"],
    expires_at=datetime.utcnow() + timedelta(days=365)
)

# 2. Show key to user ONCE
print(f"Your API key: {api_key_data['key']}")
print("Save this key securely - it won't be shown again!")

# 3. Later, verify API key in requests
try:
    key_data = await auth_service.verify_api_key(api_key)
    user_id = key_data["user_id"]
    
    if "write:pods" in key_data["scopes"]:
        # Allow operation
        pass
except HTTPException:
    # Invalid or expired key
    return {"error": "Invalid API key"}
```

### Token Refresh Pattern

```python
import httpx
from datetime import datetime, timedelta

class APIClient:
    def __init__(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = datetime.utcnow() + timedelta(minutes=30)
    
    async def request(self, method, url, **kwargs):
        # Check if token is about to expire
        if datetime.utcnow() >= self.token_expires_at - timedelta(minutes=5):
            await self.refresh_access_token()
        
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, **kwargs)
            
            # If 401, try refreshing token once
            if response.status_code == 401:
                await self.refresh_access_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = await client.request(method, url, **kwargs)
            
            return response
    
    async def refresh_access_token(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/api/v1/auth/refresh",
                json={"refresh_token": self.refresh_token}
            )
            data = response.json()
            self.access_token = data["access_token"]
            self.token_expires_at = datetime.utcnow() + timedelta(
                seconds=data["expires_in"]
            )
```

---

## Error Handling

### Common Error Responses

**400 Bad Request**:
```json
{
    "detail": "Invalid or expired token"
}
```

**401 Unauthorized**:
```json
{
    "detail": "Could not validate credentials"
}
```

**403 Forbidden**:
```json
{
    "detail": "Account is suspended or deleted"
}
```

**429 Too Many Requests**:
```json
{
    "detail": "Too many login attempts. Try again in 15 minutes."
}
```

### Error Handling Best Practices

```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

try:
    result = await auth_service.login_user(...)
except HTTPException as e:
    logger.warning(f"Login failed: {e.detail}")
    # Return user-friendly error
    raise
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    # Don't expose internal errors to user
    raise HTTPException(
        status_code=500,
        detail="An internal error occurred"
    )
```

---

## Testing

### Unit Test Examples

```python
import pytest
from auth_service import AuthenticationService

@pytest.mark.asyncio
async def test_register_user():
    auth_service = AuthenticationService()
    await auth_service.initialize()
    
    result = await auth_service.register_user(
        email="test@example.com",
        password="TestPass123!",
        first_name="Test",
        last_name="User"
    )
    
    assert "user_id" in result
    assert result["email"] == "test@example.com"
    assert result["verification_required"] == True
    
    await auth_service.close()

@pytest.mark.asyncio
async def test_login_with_invalid_credentials():
    auth_service = AuthenticationService()
    await auth_service.initialize()
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login_user(
            email="test@example.com",
            password="WrongPassword",
            ip_address="127.0.0.1",
            user_agent="Test"
        )
    
    assert exc_info.value.status_code == 401
    
    await auth_service.close()
```

### Integration Test Example

```python
from fastapi.testclient import TestClient
from auth_service import app

client = TestClient(app)

def test_complete_auth_flow():
    # Register
    response = client.post("/api/v1/auth/register", json={
        "email": "integration@example.com",
        "password": "TestPass123!",
        "first_name": "Integration",
        "last_name": "Test"
    })
    assert response.status_code == 201
    
    # Note: In real test, verify email first
    
    # Login
    response = client.post("/api/v1/auth/login", data={
        "username": "integration@example.com",
        "password": "TestPass123!"
    })
    assert response.status_code == 200
    tokens = response.json()
    
    # Verify token
    response = client.get(
        "/api/v1/auth/verify",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json()["valid"] == True
```

---

## Deployment Checklist

### Before Production

- [ ] Change `SECRET_KEY` to strong random value
- [ ] Configure production database URL
- [ ] Set up Redis cluster
- [ ] Configure email service (SMTP or provider like SendGrid)
- [ ] Register SSO applications with providers
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS properly
- [ ] Set up monitoring and alerting
- [ ] Enable rate limiting
- [ ] Configure backup strategy
- [ ] Set up log aggregation
- [ ] Document incident response procedures
- [ ] Perform security audit
- [ ] Load testing
- [ ] Set up health checks

### Production Configuration

```python
# settings.py
import os

class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    
    # Force HTTPS
    FORCE_SSL = True
    
    # Production email
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    
    # Logging
    LOG_LEVEL = "INFO"
    SENTRY_DSN = os.getenv("SENTRY_DSN")
```

---

## Monitoring & Maintenance

### Key Metrics to Monitor

1. **Authentication Metrics**:
   - Login success/failure rate
   - Average login time
   - 2FA verification rate
   - SSO provider success rate

2. **Security Metrics**:
   - Failed login attempts per minute
   - Password reset requests
   - Account lockouts
   - Suspicious activity patterns

3. **Performance Metrics**:
   - Token generation time
   - Database query time
   - Redis latency
   - Email delivery time

4. **System Health**:
   - Database connection pool usage
   - Redis memory usage
   - API response times
   - Error rates

### Maintenance Tasks

**Daily**:
- Monitor error logs
- Check failed login attempts
- Verify email delivery

**Weekly**:
- Clean up expired sessions
- Review security events
- Check API key usage

**Monthly**:
- Rotate database credentials
- Update dependencies
- Security audit
- Performance review

**Quarterly**:
- Penetration testing
- Compliance review
- Disaster recovery drill
- Update SSO integrations

---

## Support & Troubleshooting

### Common Issues

**Issue**: Users not receiving verification emails
```
Solution:
1. Check SMTP configuration
2. Verify email is not in spam
3. Check email service logs
4. Verify FROM_EMAIL domain is authorized
```

**Issue**: 2FA codes not working
```
Solution:
1. Check server time is synchronized (NTP)
2. Verify TOTP window settings
3. Check user's device time
4. Use backup codes if available
```

**Issue**: High database load
```
Solution:
1. Check for missing indexes
2. Optimize slow queries
3. Enable connection pooling
4. Consider read replicas
```

**Issue**: Redis connection errors
```
Solution:
1. Verify Redis is running
2. Check connection limits
3. Monitor memory usage
4. Consider Redis cluster
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [TOTP RFC 6238](https://tools.ietf.org/html/rfc6238)

---

# 50 REST API Use Cases for Authentication System

Complete API reference with endpoints, methods, inputs, and expected outputs.

**Base URL**: `http://localhost:8001/api/v1/auth`

---

## 1. User Registration

**Endpoint**: `/register`  
**Method**: `POST`  
**Description**: Create a new user account

**Input**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

**Expected Output** (201 Created):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "message": "User registered successfully. Please verify your email.",
  "verification_required": true
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Email already registered"
}
```

---

## 2. User Login (Email/Password)

**Endpoint**: `/login`  
**Method**: `POST`  
**Description**: Authenticate user with email and password

**Input** (form-urlencoded):
```
username=user@example.com&password=SecurePass123!
```

**Expected Output** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Output (2FA Required)**:
```json
{
  "requires_2fa": true,
  "session_token": "temp_2fa_session_token_xyz"
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Incorrect email or password"
}
```

---

## 3. Verify Email Address

**Endpoint**: `/verify-email`  
**Method**: `POST`  
**Description**: Verify user's email with token

**Input** (Query Parameter):
```
?token=verification_token_abc123xyz
```

**Expected Output** (200 OK):
```json
{
  "message": "Email verified successfully"
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Invalid verification token"
}
```

---

## 4. Resend Email Verification

**Endpoint**: `/resend-verification`  
**Method**: `POST`  
**Description**: Resend verification email to user

**Input**:
```json
{
  "email": "user@example.com"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Verification email sent"
}
```

---

## 5. Request Password Reset

**Endpoint**: `/password/reset-request`  
**Method**: `POST`  
**Description**: Request password reset link via email

**Input**:
```json
{
  "email": "user@example.com"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "If that email exists, reset instructions have been sent"
}
```

---

## 6. Reset Password with Token

**Endpoint**: `/password/reset`  
**Method**: `POST`  
**Description**: Reset password using reset token

**Input**:
```json
{
  "token": "reset_token_xyz789",
  "new_password": "NewSecurePass123!"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Password reset successfully"
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Token has expired"
}
```

---

## 7. Change Password (Authenticated)

**Endpoint**: `/password/change`  
**Method**: `POST`  
**Description**: Change password while logged in

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "old_password": "OldSecurePass123!",
  "new_password": "NewSecurePass456!"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Password changed successfully"
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Incorrect current password"
}
```

---

## 8. Logout User

**Endpoint**: `/logout`  
**Method**: `POST`  
**Description**: Logout and invalidate current session

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "message": "Logged out successfully"
}
```

---

## 9. Refresh Access Token

**Endpoint**: `/refresh`  
**Method**: `POST`  
**Description**: Get new access token using refresh token

**Input**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Expected Output** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 10. Verify Token

**Endpoint**: `/verify`  
**Method**: `GET`  
**Description**: Verify if current token is valid

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "valid": true,
  "user": {
    "sub": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "tier": "free",
    "exp": 1730000000
  }
}
```

---

## 11. Enable Two-Factor Authentication

**Endpoint**: `/2fa/enable`  
**Method**: `POST`  
**Description**: Enable 2FA for user account

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "password": "SecurePass123!"
}
```

**Expected Output** (200 OK):
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "backup_codes": [
    "abc123",
    "def456",
    "ghi789",
    "jkl012",
    "mno345",
    "pqr678",
    "stu901",
    "vwx234",
    "yza567",
    "bcd890"
  ]
}
```

---

## 12. Verify 2FA Code

**Endpoint**: `/2fa/verify`  
**Method**: `POST`  
**Description**: Verify 2FA code and complete login

**Input**:
```json
{
  "session_token": "temp_2fa_session_token_xyz",
  "code": "123456"
}
```

**Expected Output** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Invalid 2FA code"
}
```

---

## 13. Disable Two-Factor Authentication

**Endpoint**: `/2fa/disable`  
**Method**: `POST`  
**Description**: Disable 2FA for user account

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "password": "SecurePass123!",
  "code": "123456"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "2FA disabled successfully"
}
```

---

## 14. Send 2FA Code via Email

**Endpoint**: `/2fa/send-code`  
**Method**: `POST`  
**Description**: Send 2FA code to user's email (alternative to TOTP)

**Input** (Query Parameter):
```
?session_token=temp_2fa_session_token_xyz
```

**Expected Output** (200 OK):
```json
{
  "sent": true,
  "expires_in": 300
}
```

---

## 15. Regenerate 2FA Backup Codes

**Endpoint**: `/2fa/regenerate-backup-codes`  
**Method**: `POST`  
**Description**: Generate new backup codes

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "backup_codes": [
    "new123",
    "new456",
    "new789",
    "new012",
    "new345",
    "new678",
    "new901",
    "new234",
    "new567",
    "new890"
  ]
}
```

---

## 16. Initiate SSO Login (Google)

**Endpoint**: `/sso/initiate`  
**Method**: `POST`  
**Description**: Start SSO authentication flow

**Input**:
```json
{
  "provider": "google",
  "redirect_uri": "https://yourapp.com/auth/callback"
}
```

**Expected Output** (200 OK):
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&state=random_state",
  "state": "random_state_token_abc123"
}
```

---

## 17. Initiate SSO Login (GitHub)

**Endpoint**: `/sso/initiate`  
**Method**: `POST`  
**Description**: Start GitHub SSO flow

**Input**:
```json
{
  "provider": "github",
  "redirect_uri": "https://yourapp.com/auth/callback"
}
```

**Expected Output** (200 OK):
```json
{
  "authorization_url": "https://github.com/login/oauth/authorize?client_id=...&state=random_state",
  "state": "random_state_token_xyz789"
}
```

---

## 18. Handle SSO Callback

**Endpoint**: `/sso/callback`  
**Method**: `POST`  
**Description**: Complete SSO authentication

**Input**:
```json
{
  "code": "authorization_code_from_provider",
  "state": "random_state_token_abc123"
}
```

**Expected Output** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 19. List Available SSO Providers

**Endpoint**: `/sso/providers`  
**Method**: `GET`  
**Description**: Get list of supported SSO providers

**Expected Output** (200 OK):
```json
{
  "providers": [
    "google",
    "github",
    "azure",
    "okta"
  ]
}
```

---

## 20. Unlink SSO Provider

**Endpoint**: `/sso/unlink`  
**Method**: `DELETE`  
**Description**: Disconnect SSO provider from account

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "message": "SSO provider unlinked"
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Cannot unlink SSO. Please set a password first."
}
```

---

## 21. List Active Sessions

**Endpoint**: `/sessions`  
**Method**: `GET`  
**Description**: Get all active user sessions

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "sessions": [
    {
      "id": "session_id_1",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
      "created_at": "2025-10-01T10:00:00Z",
      "last_activity": "2025-10-01T12:30:00Z",
      "is_current": true
    },
    {
      "id": "session_id_2",
      "ip_address": "10.0.0.5",
      "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0...)...",
      "created_at": "2025-09-30T08:00:00Z",
      "last_activity": "2025-10-01T09:15:00Z",
      "is_current": false
    }
  ]
}
```

---

## 22. Revoke Specific Session

**Endpoint**: `/sessions/{session_id}`  
**Method**: `DELETE`  
**Description**: Revoke a specific session

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameter**:
```
session_id: "session_id_2"
```

**Expected Output** (200 OK):
```json
{
  "message": "Session revoked"
}
```

---

## 23. Revoke All Sessions Except Current

**Endpoint**: `/sessions`  
**Method**: `DELETE`  
**Description**: Logout from all devices except current

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "message": "All other sessions revoked"
}
```

---

## 24. Create API Key

**Endpoint**: `/api-keys`  
**Method**: `POST`  
**Description**: Generate a new API key

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "name": "Production API Key",
  "scopes": ["read", "write"],
  "expires_at": "2026-12-31T23:59:59Z"
}
```

**Expected Output** (200 OK):
```json
{
  "id": "key_550e8400e29b41d4a716",
  "key": "sk_live_abc123def456ghi789jkl012mno345",
  "prefix": "sk_live_abc1"
}
```

---

## 25. List API Keys

**Endpoint**: `/api-keys`  
**Method**: `GET`  
**Description**: Get all API keys for user

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "api_keys": [
    {
      "id": "key_550e8400e29b41d4a716",
      "name": "Production API Key",
      "key_prefix": "sk_live_abc1",
      "scopes": ["read", "write"],
      "created_at": "2025-01-15T10:00:00Z",
      "expires_at": "2026-12-31T23:59:59Z",
      "last_used_at": "2025-10-01T08:30:00Z",
      "is_active": true
    },
    {
      "id": "key_660f9511f39c52e5b827",
      "name": "Development Key",
      "key_prefix": "sk_test_xyz9",
      "scopes": ["read"],
      "created_at": "2025-02-20T14:30:00Z",
      "expires_at": null,
      "last_used_at": "2025-09-28T16:45:00Z",
      "is_active": true
    }
  ]
}
```

---

## 26. Revoke API Key

**Endpoint**: `/api-keys/{key_id}`  
**Method**: `DELETE`  
**Description**: Deactivate an API key

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameter**:
```
key_id: "key_550e8400e29b41d4a716"
```

**Expected Output** (200 OK):
```json
{
  "message": "API key revoked"
}
```

---

## 27. Health Check

**Endpoint**: `/health`  
**Method**: `GET`  
**Description**: Check if authentication service is running

**Expected Output** (200 OK):
```json
{
  "status": "healthy",
  "service": "authentication"
}
```

---

## 28. Get Current User Profile

**Endpoint**: `/profile`  
**Method**: `GET`  
**Description**: Get authenticated user's profile (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "avatar_url": null,
  "two_factor_enabled": true,
  "sso_provider": null,
  "status": "active",
  "tier": "pro",
  "created_at": "2025-01-15T10:00:00Z"
}
```

---

## 29. Update User Profile

**Endpoint**: `/profile`  
**Method**: `PATCH`  
**Description**: Update user profile information (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "first_name": "Jonathan",
  "last_name": "Doe",
  "phone": "+1234567891",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "Jonathan",
    "last_name": "Doe",
    "phone": "+1234567891",
    "avatar_url": "https://example.com/avatar.jpg"
  }
}
```

---

## 30. Delete User Account

**Endpoint**: `/account`  
**Method**: `DELETE`  
**Description**: Permanently delete user account (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "password": "SecurePass123!",
  "confirmation": "DELETE MY ACCOUNT"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Account deleted successfully"
}
```

---

## 31. Login with Email Code (Passwordless)

**Endpoint**: `/login/email-code/request`  
**Method**: `POST`  
**Description**: Request magic link/code for passwordless login (custom endpoint)

**Input**:
```json
{
  "email": "user@example.com"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Login code sent to your email",
  "expires_in": 600
}
```

---

## 32. Verify Email Login Code

**Endpoint**: `/login/email-code/verify`  
**Method**: `POST`  
**Description**: Verify email code and login (custom endpoint)

**Input**:
```json
{
  "email": "user@example.com",
  "code": "ABC123"
}
```

**Expected Output** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 33. Get Login History

**Endpoint**: `/login-history`  
**Method**: `GET`  
**Description**: Get user's login history (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
```
?limit=10&offset=0
```

**Expected Output** (200 OK):
```json
{
  "total": 45,
  "history": [
    {
      "timestamp": "2025-10-01T12:30:00Z",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "location": "New York, US",
      "method": "password",
      "success": true
    },
    {
      "timestamp": "2025-09-30T08:15:00Z",
      "ip_address": "10.0.0.5",
      "user_agent": "Mozilla/5.0...",
      "location": "London, UK",
      "method": "sso_google",
      "success": true
    },
    {
      "timestamp": "2025-09-29T14:20:00Z",
      "ip_address": "203.0.113.0",
      "user_agent": "curl/7.68.0",
      "location": "Unknown",
      "method": "password",
      "success": false
    }
  ]
}
```

---

## 34. Enable Account Lockout Notifications

**Endpoint**: `/security/notifications`  
**Method**: `POST`  
**Description**: Configure security notifications (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "failed_login_attempts": true,
  "new_device_login": true,
  "password_changed": true,
  "2fa_disabled": true,
  "api_key_created": true
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Security notifications updated",
  "settings": {
    "failed_login_attempts": true,
    "new_device_login": true,
    "password_changed": true,
    "2fa_disabled": true,
    "api_key_created": true
  }
}
```

---

## 35. Get Security Events

**Endpoint**: `/security/events`  
**Method**: `GET`  
**Description**: Get security-related events (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
```
?limit=20&type=login,password_change
```

**Expected Output** (200 OK):
```json
{
  "events": [
    {
      "id": "event_123",
      "type": "login",
      "timestamp": "2025-10-01T12:30:00Z",
      "ip_address": "192.168.1.1",
      "details": "Successful login from new device",
      "severity": "info"
    },
    {
      "id": "event_124",
      "type": "password_change",
      "timestamp": "2025-09-28T10:15:00Z",
      "ip_address": "192.168.1.1",
      "details": "Password changed successfully",
      "severity": "info"
    },
    {
      "id": "event_125",
      "type": "failed_login",
      "timestamp": "2025-09-27T03:45:00Z",
      "ip_address": "203.0.113.0",
      "details": "5 failed login attempts",
      "severity": "warning"
    }
  ]
}
```

---

## 36. Verify Phone Number (Send Code)

**Endpoint**: `/phone/verify/send`  
**Method**: `POST`  
**Description**: Send verification code to phone (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "phone": "+1234567890"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Verification code sent",
  "expires_in": 300
}
```

---

## 37. Verify Phone Number (Confirm Code)

**Endpoint**: `/phone/verify/confirm`  
**Method**: `POST`  
**Description**: Verify phone with code (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "phone": "+1234567890",
  "code": "123456"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Phone verified successfully",
  "phone": "+1234567890",
  "verified": true
}
```

---

## 38. Set Account Recovery Email

**Endpoint**: `/recovery/email`  
**Method**: `POST`  
**Description**: Set backup email for account recovery (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "recovery_email": "backup@example.com",
  "password": "SecurePass123!"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Recovery email set successfully",
  "recovery_email": "backup@example.com"
}
```

---

## 39. Get Account Security Score

**Endpoint**: `/security/score`  
**Method**: `GET`  
**Description**: Get account security rating (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "score": 85,
  "max_score": 100,
  "rating": "good",
  "factors": {
    "strong_password": true,
    "2fa_enabled": true,
    "email_verified": true,
    "phone_verified": false,
    "recovery_email_set": true,
    "recent_password_change": false
  },
  "recommendations": [
    "Verify your phone number for additional security",
    "Change your password (last changed 180 days ago)"
  ]
}
```

---

## 40. Export User Data (GDPR)

**Endpoint**: `/data/export`  
**Method**: `POST`  
**Description**: Request data export (GDPR compliance) (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (202 Accepted):
```json
{
  "message": "Data export requested. You will receive an email when ready.",
  "request_id": "export_550e8400e29b41d4a716",
  "estimated_time": "24 hours"
}
```

---

## 41. Check Email Availability

**Endpoint**: `/check/email`  
**Method**: `GET`  
**Description**: Check if email is available for registration (custom endpoint)

**Query Parameters**:
```
?email=newuser@example.com
```

**Expected Output** (200 OK):
```json
{
  "available": true,
  "email": "newuser@example.com"
}
```

**If Taken**:
```json
{
  "available": false,
  "email": "existing@example.com",
  "message": "Email already registered"
}
```

---

## 42. Rate Limit Status

**Endpoint**: `/rate-limit/status`  
**Method**: `GET`  
**Description**: Check rate limit status for current IP (custom endpoint)

**Expected Output** (200 OK):
```json
{
  "ip_address": "192.168.1.1",
  "remaining_requests": 95,
  "limit": 100,
  "reset_at": "2025-10-01T13:00:00Z",
  "window": "1 hour"
}
```

---

## 43. Link Social Media Account

**Endpoint**: `/social/link`  
**Method**: `POST`  
**Description**: Link social media to existing account (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "provider": "twitter",
  "provider_user_id": "twitter_user_123",
  "access_token": "twitter_access_token"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Social account linked successfully",
  "provider": "twitter",
  "linked_at": "2025-10-01T12:00:00Z"
}
```

---

## 44. Get Linked Social Accounts

**Endpoint**: `/social/linked`  
**Method**: `GET`  
**Description**: List all linked social accounts (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "linked_accounts": [
    {
      "provider": "google",
      "provider_user_id": "google_123",
      "email": "user@gmail.com",
      "linked_at": "2025-01-15T10:00:00Z"
    },
    {
      "provider": "github",
      "provider_user_id": "github_456",
      "username": "johndoe",
      "linked_at": "2025-03-20T14:30:00Z"
    }
  ]
}
```

---

## 45. Unlink Social Account

**Endpoint**: `/social/unlink`  
**Method**: `DELETE`  
**Description**: Remove linked social account (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "provider": "twitter"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Social account unlinked successfully",
  "provider": "twitter"
}
```

---

## 46. Get User Permissions

**Endpoint**: `/permissions`  
**Method**: `GET`  
**Description**: Get user's permissions/roles (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "roles": ["user", "admin"],
  "permissions": [
    "read:users",
    "write:users",
    "delete:users",
    "read:analytics",
    "manage:api_keys"
  ]
}
```

---

## 47. Accept Terms of Service

**Endpoint**: `/legal/accept-terms`  
**Method**: `POST`  
**Description**: Accept terms of service (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "version": "2.0",
  "accepted": true,
  "ip_address": "192.168.1.1"
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Terms accepted",
  "version": "2.0",
  "accepted_at": "2025-10-01T12:00:00Z"
}
```

---

## 48. Get Privacy Settings

**Endpoint**: `/privacy/settings`  
**Method**: `GET`  
**Description**: Get user's privacy preferences (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Expected Output** (200 OK):
```json
{
  "profile_visibility": "private",
  "show_email": false,
  "show_phone": false,
  "allow_analytics": true,
  "allow_marketing_emails": false,
  "allow_third_party_cookies": false,
  "data_retention_days": 90
}
```

---

## 49. Update Privacy Settings

**Endpoint**: `/privacy/settings`  
**Method**: `PATCH`  
**Description**: Update privacy preferences (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "profile_visibility": "public",
  "show_email": true,
  "allow_marketing_emails": true
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Privacy settings updated",
  "settings": {
    "profile_visibility": "public",
    "show_email": true,
    "show_phone": false,
    "allow_analytics": true,
    "allow_marketing_emails": true,
    "allow_third_party_cookies": false,
    "data_retention_days": 90
  }
}
```

---

## 50. Deactivate Account (Temporary)

**Endpoint**: `/account/deactivate`  
**Method**: `POST`  
**Description**: Temporarily deactivate account (custom endpoint)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Input**:
```json
{
  "password": "SecurePass123!",
  "reason": "Taking a break",
  "duration_days": 30
}
```

**Expected Output** (200 OK):
```json
{
  "message": "Account deactivated successfully",
  "deactivated_at": "2025-10-01T12:00:00Z",
  "reactivation_date": "2025-10-31T12:00:00Z",
  "reason": "Taking a break"
}
```

---

## Summary Table

| # | Endpoint | Method | Purpose | Auth Required |
|---|----------|--------|---------|---------------|
| 1 | `/register` | POST | User registration | No |
| 2 | `/login` | POST | Email/password login | No |
| 3 | `/verify-email` | POST | Verify email address | No |
| 4 | `/resend-verification` | POST | Resend verification email | No |
| 5 | `/password/reset-request` | POST | Request password reset | No |
| 6 | `/password/reset` | POST | Reset password with token | No |
| 7 | `/password/change` | POST | Change password | Yes |
| 8 | `/logout` | POST | Logout user | Yes |
| 9 | `/refresh` | POST | Refresh access token | No |
| 10 | `/verify` | GET | Verify token validity | Yes |
| 11 | `/2fa/enable` | POST | Enable 2FA | Yes |
| 12 | `/2fa/verify` | POST | Verify 2FA code | No |
| 13 | `/2fa/disable` | POST | Disable 2FA | Yes |
| 14 | `/2fa/send-code` | POST | Send 2FA email code | No |
| 15 | `/2fa/regenerate-backup-codes` | POST | Regenerate backup codes | Yes |
| 16 | `/sso/initiate` | POST | Start Google SSO | No |
| 17 | `/sso/initiate` | POST | Start GitHub SSO | No |
| 18 | `/sso/callback` | POST | Complete SSO login | No |
| 19 | `/sso/providers` | GET | List SSO providers | No |
| 20 | `/sso/unlink` | DELETE | Unlink SSO provider | Yes |
| 21 | `/sessions` | GET | List active sessions | Yes |
| 22 | `/sessions/{id}` | DELETE | Revoke specific session | Yes |
| 23 | `/sessions` | DELETE | Revoke all sessions | Yes |
| 24 | `/api-keys` | POST | Create API key | Yes |
| 25 | `/api-keys` | GET | List API keys | Yes |
| 26 | `/api-keys/{id}` | DELETE | Revoke API key | Yes |
| 27 | `/health` | GET | Health check | No |
| 28 | `/profile` | GET | Get user profile | Yes |
| 29 | `/profile` | PATCH | Update profile | Yes |
| 30 | `/account` | DELETE | Delete account | Yes |
| 31 | `/login/email-code/request` | POST | Request passwordless login | No |
| 32 | `/login/email-code/verify` | POST | Verify email code | No |
| 33 | `/login-history` | GET | Get login history | Yes |
| 34 | `/security/notifications` | POST | Configure security alerts | Yes |
| 35 | `/security/events` | GET | Get security events | Yes |
| 36 | `/phone/verify/send` | POST | Send phone verification | Yes |
| 37 | `/phone/verify/confirm` | POST | Confirm phone code | Yes |
| 38 | `/recovery/email` | POST | Set recovery email | Yes |
| 39 | `/security/score` | GET | Get security score | Yes |
| 40 | `/data/export` | POST | Export user data (GDPR) | Yes |
| 41 | `/check/email` | GET | Check email availability | No |
| 42 | `/rate-limit/status` | GET | Check rate limit | No |
| 43 | `/social/link` | POST | Link social account | Yes |
| 44 | `/social/linked` | GET | List linked accounts | Yes |
| 45 | `/social/unlink` | DELETE | Unlink social account | Yes |
| 46 | `/permissions` | GET | Get user permissions | Yes |
| 47 | `/legal/accept-terms` | POST | Accept terms of service | Yes |
| 48 | `/privacy/settings` | GET | Get privacy settings | Yes |
| 49 | `/privacy/settings` | PATCH | Update privacy settings | Yes |
| 50 | `/account/deactivate` | POST | Deactivate account | Yes |

---

## Implementation Notes

### Base URL
All endpoints use the base URL: `http://localhost:8001/api/v1/auth`

### Authentication Header Format
For protected endpoints, use:
```
Authorization: Bearer {access_token}
```

### Error Response Format
All errors follow this structure:
```json
{
  "detail": "Error message here"
}
```

### Common HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created
- `202 Accepted` - Request accepted (async processing)
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Custom Endpoints (Not in Original Code)
Use cases 28-50 are custom endpoints that would need to be implemented. They represent common features needed in production authentication systems.

---

## Quick Integration Guide

### React/TypeScript Example

```typescript
// api/auth.ts
const BASE_URL = 'http://localhost:8001/api/v1/auth';

export const authApi = {
  async register(data: RegisterInput) {
    const response = await fetch(`${BASE_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },

  async login(email: string, password: string) {
    const response = await fetch(`${BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password })
    });
    return response.json();
  },

  async getProfile(token: string) {
    const response = await fetch(`${BASE_URL}/profile`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  }
};
```

### Python Example

```python
import httpx

BASE_URL = "http://localhost:8001/api/v1/auth"

async def register(email, password, first_name, last_name):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/register",
            json={
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name
            }
        )
        return response.json()
```

---

## Testing with cURL

```bash
# Register
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","first_name":"Test","last_name":"User"}'

# Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=Test123!"

# Protected endpoint
curl -X GET http://localhost:8001/api/v1/auth/sessions \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```