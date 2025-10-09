"""
Complete Authentication & Authorization System for SaaS Platform
File: auth_service.py
"""

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
import pyotp
import qrcode
import io
import base64
import redis
import asyncpg
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import hashlib
from enum import Enum
import uuid
import httpx
import logging

# ============================================================================
# CONFIGURATION
# ============================================================================

class Settings:
    # JWT Settings
    SECRET_KEY = "your-secret-key-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Database
    DATABASE_URL = "postgresql://user:password@localhost/saas_db"
    
    # Redis
    REDIS_URL = "redis://localhost:6379"
    
    # Email
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "your-email@gmail.com"
    SMTP_PASSWORD = "your-password"
    FROM_EMAIL = "noreply@yoursaas.com"
    
    # SSO
    GOOGLE_CLIENT_ID = "your-google-client-id"
    GOOGLE_CLIENT_SECRET = "your-google-secret"
    GITHUB_CLIENT_ID = "your-github-client-id"
    GITHUB_CLIENT_SECRET = "your-github-secret"
    
    # 2FA
    TOTP_ISSUER = "YourSaaS"
    TWO_FA_CODE_EXPIRE_MINUTES = 5
    
    # Security
    PASSWORD_MIN_LENGTH = 8
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

settings = Settings()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class UserTier(str, Enum):
    FREE = "free"
    NORMAL = "normal"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class SSOProvider(str, Enum):
    GOOGLE = "google"
    GITHUB = "github"
    AZURE = "azure"
    OKTA = "okta"

# Request Models
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    phone: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {settings.PASSWORD_MIN_LENGTH} characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class SSOInitiateRequest(BaseModel):
    provider: SSOProvider
    redirect_uri: str

class SSOCallbackRequest(BaseModel):
    code: str
    state: str

class TwoFactorEnableRequest(BaseModel):
    password: str

class TwoFactorVerifyRequest(BaseModel):
    code: str
    session_token: str

class TwoFactorDisableRequest(BaseModel):
    password: str
    code: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

class APIKeyCreateRequest(BaseModel):
    name: str
    scopes: List[str]
    expires_at: Optional[datetime] = None

# Response Models
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    avatar_url: Optional[str]
    two_factor_enabled: bool
    sso_provider: Optional[str]
    status: str
    tier: str
    created_at: datetime

class SessionResponse(BaseModel):
    id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    is_current: bool

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]

# ============================================================================
# AUTHENTICATION SERVICE CLASS
# ============================================================================

class AuthenticationService:
    """
    Complete Authentication & Authorization Service
    Handles all auth operations including SSO, 2FA, sessions, and API keys
    """
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.redis_client = None
        self.db_pool = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize database and Redis connections"""
        # Initialize Redis
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Initialize PostgreSQL connection pool
        self.db_pool = await asyncpg.create_pool(settings.DATABASE_URL)
        
    async def close(self):
        """Close connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.db_pool:
            await self.db_pool.close()
    
    # ========================================================================
    # DATABASE HELPER METHODS
    # ========================================================================
    
    def get_table_name(self, base_table: str, user_tier: str, user_id: str = None) -> str:
        """
        Get appropriate table name based on user tier
        Free/Normal: nexus_{user_id}_{table_name}
        Pro/Enterprise: {table_name} (separate database)
        """
        if user_tier in [UserTier.FREE.value, UserTier.NORMAL.value]:
            if user_id:
                return f"nexus_{user_id}_{base_table}"
            return base_table  # For main users table
        return base_table
    
    async def get_db_connection(self, user_tier: str):
        """Get database connection based on user tier"""
        # For Pro/Enterprise, you would connect to their dedicated database
        # For now, using the same pool
        return await self.db_pool.acquire()
    
    # ========================================================================
    # PASSWORD HASHING
    # ========================================================================
        
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return self.pwd_context.hash(password)
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    # ========================================================================
    # JWT TOKEN MANAGEMENT
    # ========================================================================
    
    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Check if token is blacklisted
            is_blacklisted = await self.redis_client.get(f"blacklist:{token}")
            if is_blacklisted:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def blacklist_token(self, token: str, expires_in: int):
        """Add token to blacklist"""
        await self.redis_client.setex(
            f"blacklist:{token}",
            expires_in,
            "1"
        )
    
    # ========================================================================
    # USER REGISTRATION & LOGIN
    # ========================================================================
    
    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a new user"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            # Check if user already exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                email
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            hashed_password = self.hash_password(password)
            
            # Create user
            user_id = str(uuid.uuid4())
            user = await conn.fetchrow(
                """
                INSERT INTO users (
                    id, email, password_hash, first_name, last_name,
                    phone, status, email_verified, tier
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id, email, first_name, last_name, created_at
                """,
                user_id, email, hashed_password, first_name, last_name,
                phone, UserStatus.ACTIVE.value, False, UserTier.FREE.value
            )
            
            # Generate email verification token
            verification_token = secrets.token_urlsafe(32)
            await conn.execute(
                """
                INSERT INTO email_verification_tokens (user_id, token, expires_at)
                VALUES ($1, $2, $3)
                """,
                user_id,
                verification_token,
                datetime.utcnow() + timedelta(hours=24)
            )
            
            # Send verification email (background task)
            await self.send_verification_email(email, verification_token)
            
            return {
                "user_id": user_id,
                "email": email,
                "message": "User registered successfully. Please verify your email.",
                "verification_required": True
            }
            
        finally:
            await self.db_pool.release(conn)
    
    async def login_user(
        self,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """Login user with email and password"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            # Check login attempts
            attempts_key = f"login_attempts:{email}"
            attempts = await self.redis_client.get(attempts_key)
            
            if attempts and int(attempts) >= settings.MAX_LOGIN_ATTEMPTS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many login attempts. Try again in {settings.LOCKOUT_DURATION_MINUTES} minutes."
                )
            
            # Get user
            user = await conn.fetchrow(
                """
                SELECT id, email, password_hash, two_factor_enabled, 
                       status, tier, email_verified
                FROM users
                WHERE email = $1
                """,
                email
            )
            
            if not user or not self.verify_password(password, user['password_hash']):
                # Increment failed attempts
                await self.redis_client.incr(attempts_key)
                await self.redis_client.expire(
                    attempts_key,
                    settings.LOCKOUT_DURATION_MINUTES * 60
                )
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            # Check user status
            if user['status'] != UserStatus.ACTIVE.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is suspended or deleted"
                )
            
            # Check email verification
            if not user['email_verified']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Please verify your email before logging in"
                )
            
            # Clear login attempts
            await self.redis_client.delete(attempts_key)
            
            # Check if 2FA is enabled
            if user['two_factor_enabled']:
                # Generate session token for 2FA verification
                session_token = secrets.token_urlsafe(32)
                await self.redis_client.setex(
                    f"2fa_session:{session_token}",
                    600,  # 10 minutes
                    user['id']
                )
                
                return {
                    "requires_2fa": True,
                    "session_token": session_token
                }
            
            # Create tokens
            access_token = self.create_access_token(
                data={"sub": user['id'], "email": user['email'], "tier": user['tier']}
            )
            refresh_token = self.create_refresh_token(
                data={"sub": user['id']}
            )
            
            # Create session
            session_id = await self.create_session(
                user['id'],
                access_token,
                refresh_token,
                ip_address,
                user_agent
            )
            
            # Update last login
            await conn.execute(
                "UPDATE users SET last_login_at = $1 WHERE id = $2",
                datetime.utcnow(),
                user['id']
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        finally:
            await self.db_pool.release(conn)
    
    async def logout_user(self, token: str, user_id: str):
        """Logout user and invalidate token"""
        # Blacklist the token
        payload = await self.verify_token(token)
        exp = payload.get("exp")
        current_time = datetime.utcnow().timestamp()
        expires_in = int(exp - current_time)
        
        if expires_in > 0:
            await self.blacklist_token(token, expires_in)
        
        # Remove session
        conn = await self.get_db_connection(UserTier.FREE.value)
        try:
            await conn.execute(
                "DELETE FROM user_sessions WHERE token = $1",
                token
            )
        finally:
            await self.db_pool.release(conn)
    
    # ========================================================================
    # EMAIL VERIFICATION
    # ========================================================================
    
    async def verify_email(self, token: str) -> bool:
        """Verify user email with token"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            # Get token
            token_record = await conn.fetchrow(
                """
                SELECT user_id, expires_at, used_at
                FROM email_verification_tokens
                WHERE token = $1
                """,
                token
            )
            
            if not token_record:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification token"
                )
            
            if token_record['used_at']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token already used"
                )
            
            if datetime.utcnow() > token_record['expires_at']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token has expired"
                )
            
            # Mark email as verified
            await conn.execute(
                "UPDATE users SET email_verified = TRUE WHERE id = $1",
                token_record['user_id']
            )
            
            # Mark token as used
            await conn.execute(
                "UPDATE email_verification_tokens SET used_at = $1 WHERE token = $2",
                datetime.utcnow(),
                token
            )
            
            return True
            
        finally:
            await self.db_pool.release(conn)
    
    async def resend_verification_email(self, email: str):
        """Resend verification email"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            user = await conn.fetchrow(
                "SELECT id, email_verified FROM users WHERE email = $1",
                email
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if user['email_verified']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already verified"
                )
            
            # Generate new token
            verification_token = secrets.token_urlsafe(32)
            await conn.execute(
                """
                INSERT INTO email_verification_tokens (user_id, token, expires_at)
                VALUES ($1, $2, $3)
                """,
                user['id'],
                verification_token,
                datetime.utcnow() + timedelta(hours=24)
            )
            
            await self.send_verification_email(email, verification_token)
            
        finally:
            await self.db_pool.release(conn)
    
    # ========================================================================
    # PASSWORD RESET
    # ========================================================================
    
    async def request_password_reset(self, email: str):
        """Request password reset"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            user = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                email
            )
            
            if not user:
                # Don't reveal if email exists
                return
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            await conn.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES ($1, $2, $3)
                """,
                user['id'],
                reset_token,
                datetime.utcnow() + timedelta(hours=1)
            )
            
            await self.send_password_reset_email(email, reset_token)
            
        finally:
            await self.db_pool.release(conn)
    
    async def reset_password(self, token: str, new_password: str):
        """Reset password with token"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            # Get token
            token_record = await conn.fetchrow(
                """
                SELECT user_id, expires_at, used_at
                FROM password_reset_tokens
                WHERE token = $1
                """,
                token
            )
            
            if not token_record:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token"
                )
            
            if token_record['used_at']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token already used"
                )
            
            if datetime.utcnow() > token_record['expires_at']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token has expired"
                )
            
            # Hash new password
            hashed_password = self.hash_password(new_password)
            
            # Update password
            await conn.execute(
                "UPDATE users SET password_hash = $1 WHERE id = $2",
                hashed_password,
                token_record['user_id']
            )
            
            # Mark token as used
            await conn.execute(
                "UPDATE password_reset_tokens SET used_at = $1 WHERE token = $2",
                datetime.utcnow(),
                token
            )
            
            # Invalidate all sessions for security
            await conn.execute(
                "DELETE FROM user_sessions WHERE user_id = $1",
                token_record['user_id']
            )
            
        finally:
            await self.db_pool.release(conn)
    
    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ):
        """Change password (when logged in)"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            user = await conn.fetchrow(
                "SELECT password_hash FROM users WHERE id = $1",
                user_id
            )
            
            if not self.verify_password(old_password, user['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect current password"
                )
            
            hashed_password = self.hash_password(new_password)
            await conn.execute(
                "UPDATE users SET password_hash = $1 WHERE id = $2",
                hashed_password,
                user_id
            )
            
        finally:
            await self.db_pool.release(conn)
    
    # ========================================================================
    # TWO-FACTOR AUTHENTICATION (2FA)
    # ========================================================================
    
    async def enable_2fa(self, user_id: str, password: str) -> Dict[str, Any]:
        """Enable 2FA for user"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            # Verify password
            user = await conn.fetchrow(
                "SELECT email, password_hash, two_factor_enabled FROM users WHERE id = $1",
                user_id
            )
            
            if not self.verify_password(password, user['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect password"
                )
            
            if user['two_factor_enabled']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="2FA already enabled"
                )
            
            # Generate TOTP secret
            secret = pyotp.random_base32()
            
            # Generate QR code
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user['email'],
                issuer_name=settings.TOTP_ISSUER
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Generate backup codes
            backup_codes = [secrets.token_hex(3) for _ in range(10)]  # 6 chars instead of 8
            hashed_codes = [self.hash_password(code) for code in backup_codes]
            
            # Store secret and backup codes
            await conn.execute(
                """
                UPDATE users 
                SET two_factor_secret = $1,
                    backup_codes = $2,
                    two_factor_enabled = TRUE
                WHERE id = $3
                """,
                secret,
                hashed_codes,
                user_id
            )
            
            return {
                "secret": secret,
                "qr_code": f"data:image/png;base64,{qr_code_base64}",
                "backup_codes": backup_codes
            }
            
        finally:
            await self.db_pool.release(conn)
    
    async def verify_2fa(
        self,
        session_token: str,
        code: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """Verify 2FA code and complete login"""
        # Get user_id from session token
        user_id = await self.redis_client.get(f"2fa_session:{session_token}")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired session token"
            )
        
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            user = await conn.fetchrow(
                """
                SELECT id, email, two_factor_secret, backup_codes, tier
                FROM users
                WHERE id = $1
                """,
                user_id
            )
            
            # Verify TOTP code
            totp = pyotp.TOTP(user['two_factor_secret'])
            is_valid = totp.verify(code, valid_window=1)
            
            # If TOTP fails, try backup codes
            if not is_valid:
                for hashed_code in user['backup_codes']:
                    if self.verify_password(code, hashed_code):
                        is_valid = True
                        # Remove used backup code
                        remaining_codes = [
                            c for c in user['backup_codes'] 
                            if c != hashed_code
                        ]
                        await conn.execute(
                            "UPDATE users SET backup_codes = $1 WHERE id = $2",
                            remaining_codes,
                            user_id
                        )
                        break
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid 2FA code"
                )
            
            # Create tokens
            access_token = self.create_access_token(
                data={"sub": user['id'], "email": user['email'], "tier": user['tier']}
            )
            refresh_token = self.create_refresh_token(
                data={"sub": user['id']}
            )
            
            # Create session
            await self.create_session(
                user['id'],
                access_token,
                refresh_token,
                ip_address,
                user_agent
            )
            
            # Delete 2FA session
            await self.redis_client.delete(f"2fa_session:{session_token}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        finally:
            await self.db_pool.release(conn)
    
    async def disable_2fa(self, user_id: str, password: str, code: str):
        """Disable 2FA"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            user = await conn.fetchrow(
                """
                SELECT password_hash, two_factor_secret, two_factor_enabled
                FROM users WHERE id = $1
                """,
                user_id
            )
            
            if not user['two_factor_enabled']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="2FA not enabled"
                )
            
            if not self.verify_password(password, user['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect password"
                )
            
            # Verify 2FA code
            totp = pyotp.TOTP(user['two_factor_secret'])
            if not totp.verify(code, valid_window=1):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid 2FA code"
                )
            
            # Disable 2FA
            await conn.execute(
                """
                UPDATE users 
                SET two_factor_enabled = FALSE,
                    two_factor_secret = NULL,
                    backup_codes = NULL
                WHERE id = $1
                """,
                user_id
            )
            
        finally:
            await self.db_pool.release(conn)
    
    async def send_2fa_email(self, session_token: str, email: str):
        """Send 2FA code via email (alternative to TOTP)"""
        user_id = await self.redis_client.get(f"2fa_session:{session_token}")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session token"
            )
        
        # Generate 6-digit code
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Store code in Redis with expiration
        await self.redis_client.setex(
            f"2fa_email_code:{session_token}",
            settings.TWO_FA_CODE_EXPIRE_MINUTES * 60,
            code
        )
        
        # Send email
        await self.send_2fa_code_email(email, code)
        
        return {
            "sent": True,
            "expires_in": settings.TWO_FA_CODE_EXPIRE_MINUTES * 60
        }
    
    async def regenerate_backup_codes(self, user_id: str) -> List[str]:
        """Regenerate 2FA backup codes"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            # Generate new backup codes
            backup_codes = [secrets.token_hex(3) for _ in range(10)]  # 6 chars instead of 8
            hashed_codes = [self.hash_password(code) for code in backup_codes]
            
            await conn.execute(
                "UPDATE users SET backup_codes = $1 WHERE id = $2",
                hashed_codes,
                user_id
            )
            
            return backup_codes
            
        finally:
            await self.db_pool.release(conn)
    
    # ========================================================================
    # SSO (Single Sign-On)
    # ========================================================================
    
    async def initiate_sso(
        self,
        provider: str,
        redirect_uri: str
    ) -> Dict[str, str]:
        """Initiate SSO flow"""
        state = secrets.token_urlsafe(32)
        
        # Store state in Redis
        await self.redis_client.setex(
            f"sso_state:{state}",
            600,  # 10 minutes
            provider
        )
        
        if provider == SSOProvider.GOOGLE.value:
            auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={settings.GOOGLE_CLIENT_ID}&"
                f"redirect_uri={redirect_uri}&"
                f"response_type=code&"
                f"scope=openid email profile&"
                f"state={state}"
            )
        elif provider == SSOProvider.GITHUB.value:
            auth_url = (
                f"https://github.com/login/oauth/authorize?"
                f"client_id={settings.GITHUB_CLIENT_ID}&"
                f"redirect_uri={redirect_uri}&"
                f"scope=user:email&"
                f"state={state}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported SSO provider"
            )
        
        return {
            "authorization_url": auth_url,
            "state": state
        }
    
    async def handle_sso_callback(
        self,
        code: str,
        state: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """Handle SSO callback"""
        # Verify state
        provider = await self.redis_client.get(f"sso_state:{state}")
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state"
            )
        
        # Exchange code for access token and get user info
        user_info = await self.exchange_sso_code(provider, code)
        
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            # Check if user exists
            user = await conn.fetchrow(
                """
                SELECT id, email, status, tier
                FROM users
                WHERE sso_provider = $1 AND sso_provider_id = $2
                """,
                provider,
                user_info['id']
            )
            
            if not user:
                # Check if email exists
                user = await conn.fetchrow(
                    "SELECT id FROM users WHERE email = $1",
                    user_info['email']
                )
                
                if user:
                    # Link SSO to existing account
                    await conn.execute(
                        """
                        UPDATE users 
                        SET sso_provider = $1, sso_provider_id = $2
                        WHERE id = $3
                        """,
                        provider,
                        user_info['id'],
                        user['id']
                    )
                else:
                    # Create new user
                    user_id = str(uuid.uuid4())
                    user = await conn.fetchrow(
                        """
                        INSERT INTO users (
                            id, email, first_name, last_name,
                            sso_provider, sso_provider_id,
                            email_verified, status, tier
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id, email, status, tier
                        """,
                        user_id,
                        user_info['email'],
                        user_info.get('first_name', ''),
                        user_info.get('last_name', ''),
                        provider,
                        user_info['id'],
                        True,  # SSO emails are pre-verified
                        UserStatus.ACTIVE.value,
                        UserTier.FREE.value
                    )
            
            # Check user status
            if user['status'] != UserStatus.ACTIVE.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is suspended or deleted"
                )
            
            # Create tokens
            access_token = self.create_access_token(
                data={"sub": user['id'], "email": user['email'], "tier": user['tier']}
            )
            refresh_token = self.create_refresh_token(
                data={"sub": user['id']}
            )
            
            # Create session
            await self.create_session(
                user['id'],
                access_token,
                refresh_token,
                ip_address,
                user_agent
            )
            
            # Delete state
            await self.redis_client.delete(f"sso_state:{state}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        finally:
            await self.db_pool.release(conn)
    
    async def exchange_sso_code(
        self,
        provider: str,
        code: str
    ) -> Dict[str, Any]:
        """Exchange SSO authorization code for user info"""
        async with httpx.AsyncClient() as client:
            if provider == SSOProvider.GOOGLE.value:
                # Exchange code for token
                token_response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "grant_type": "authorization_code"
                    }
                )
                token_data = token_response.json()
                
                # Get user info
                user_response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {token_data['access_token']}"}
                )
                user_data = user_response.json()
                
                return {
                    "id": user_data['id'],
                    "email": user_data['email'],
                    "first_name": user_data.get('given_name', ''),
                    "last_name": user_data.get('family_name', '')
                }
                
            elif provider == SSOProvider.GITHUB.value:
                # Exchange code for token
                token_response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "code": code,
                        "client_id": settings.GITHUB_CLIENT_ID,
                        "client_secret": settings.GITHUB_CLIENT_SECRET
                    },
                    headers={"Accept": "application/json"}
                )
                token_data = token_response.json()
                
                # Get user info
                user_response = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {token_data['access_token']}"}
                )
                user_data = user_response.json()
                
                # Get email (might be separate call)
                email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"token {token_data['access_token']}"}
                )
                emails = email_response.json()
                primary_email = next(
                    (e['email'] for e in emails if e['primary']),
                    emails[0]['email'] if emails else None
                )
                
                return {
                    "id": str(user_data['id']),
                    "email": primary_email,
                    "first_name": user_data.get('name', '').split()[0] if user_data.get('name') else '',
                    "last_name": user_data.get('name', '').split()[-1] if user_data.get('name') else ''
                }
    
    async def link_sso_provider(
        self,
        user_id: str,
        provider: str,
        provider_user_id: str
    ):
        """Link SSO provider to existing account"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            await conn.execute(
                """
                UPDATE users 
                SET sso_provider = $1, sso_provider_id = $2
                WHERE id = $3
                """,
                provider,
                provider_user_id,
                user_id
            )
        finally:
            await self.db_pool.release(conn)
    
    async def unlink_sso_provider(self, user_id: str):
        """Unlink SSO provider"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            # Check if user has password (can't unlink if no password)
            user = await conn.fetchrow(
                "SELECT password_hash FROM users WHERE id = $1",
                user_id
            )
            
            if not user['password_hash']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot unlink SSO. Please set a password first."
                )
            
            await conn.execute(
                """
                UPDATE users 
                SET sso_provider = NULL, sso_provider_id = NULL
                WHERE id = $1
                """,
                user_id
            )
        finally:
            await self.db_pool.release(conn)
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    async def create_session(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        ip_address: str,
        user_agent: str
    ) -> str:
        """Create user session"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            session_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
            await conn.execute(
                """
                INSERT INTO user_sessions (
                    id, user_id, token, refresh_token,
                    ip_address, user_agent, expires_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                session_id,
                user_id,
                access_token,
                refresh_token,
                ip_address,
                user_agent,
                expires_at
            )
            
            return session_id
            
        finally:
            await self.db_pool.release(conn)
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for user"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            sessions = await conn.fetch(
                """
                SELECT id, ip_address, user_agent, created_at, last_activity_at
                FROM user_sessions
                WHERE user_id = $1 AND expires_at > $2
                ORDER BY last_activity_at DESC
                """,
                user_id,
                datetime.utcnow()
            )
            
            return [dict(s) for s in sessions]
            
        finally:
            await self.db_pool.release(conn)
    
    async def revoke_session(self, session_id: str, user_id: str):
        """Revoke specific session"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            await conn.execute(
                "DELETE FROM user_sessions WHERE id = $1 AND user_id = $2",
                session_id,
                user_id
            )
        finally:
            await self.db_pool.release(conn)
    
    async def revoke_all_sessions(self, user_id: str, except_token: str = None):
        """Revoke all sessions except current"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            if except_token:
                await conn.execute(
                    "DELETE FROM user_sessions WHERE user_id = $1 AND token != $2",
                    user_id,
                    except_token
                )
            else:
                await conn.execute(
                    "DELETE FROM user_sessions WHERE user_id = $1",
                    user_id
                )
        finally:
            await self.db_pool.release(conn)
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        payload = await self.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            # Get user info
            user = await conn.fetchrow(
                "SELECT id, email, tier FROM users WHERE id = $1",
                user_id
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Create new access token
            new_access_token = self.create_access_token(
                data={"sub": user['id'], "email": user['email'], "tier": user['tier']}
            )
            
            # Update session
            await conn.execute(
                """
                UPDATE user_sessions 
                SET token = $1, last_activity_at = $2
                WHERE refresh_token = $3
                """,
                new_access_token,
                datetime.utcnow(),
                refresh_token
            )
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        finally:
            await self.db_pool.release(conn)
    
    # ========================================================================
    # API KEY MANAGEMENT
    # ========================================================================
    
    async def create_api_key(
        self,
        user_id: str,
        organization_id: str,
        name: str,
        scopes: List[str],
        expires_at: Optional[datetime] = None
    ) -> Dict[str, str]:
        """Create API key"""
        # Generate API key
        api_key = f"sk_{'test' if settings.SECRET_KEY == 'test' else 'live'}_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_prefix = api_key[:12]
        
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            key_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO api_keys (
                    id, user_id, organization_id, name,
                    key_hash, key_prefix, scopes, expires_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                key_id,
                user_id,
                organization_id,
                name,
                key_hash,
                key_prefix,
                scopes,
                expires_at
            )
            
            return {
                "id": key_id,
                "key": api_key,  # Only returned once!
                "prefix": key_prefix
            }
            
        finally:
            await self.db_pool.release(conn)
    
    async def list_api_keys(
        self,
        user_id: str,
        organization_id: str
    ) -> List[Dict[str, Any]]:
        """List user's API keys"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            keys = await conn.fetch(
                """
                SELECT id, name, key_prefix, scopes, created_at,
                       expires_at, last_used_at, is_active
                FROM api_keys
                WHERE user_id = $1 AND organization_id = $2 AND is_active = TRUE
                ORDER BY created_at DESC
                """,
                user_id,
                organization_id
            )
            
            return [dict(k) for k in keys]
            
        finally:
            await self.db_pool.release(conn)
    
    async def revoke_api_key(self, key_id: str, user_id: str):
        """Revoke API key"""
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            await conn.execute(
                """
                UPDATE api_keys 
                SET is_active = FALSE 
                WHERE id = $1 AND user_id = $2
                """,
                key_id,
                user_id
            )
        finally:
            await self.db_pool.release(conn)
    
    async def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """Verify API key and return associated user/org"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        conn = await self.get_db_connection(UserTier.FREE.value)
        
        try:
            key_record = await conn.fetchrow(
                """
                SELECT user_id, organization_id, scopes, expires_at, is_active
                FROM api_keys
                WHERE key_hash = $1
                """,
                key_hash
            )
            
            if not key_record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
            
            if not key_record['is_active']:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has been revoked"
                )
            
            if key_record['expires_at'] and datetime.utcnow() > key_record['expires_at']:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired"
                )
            
            # Update last used
            await conn.execute(
                "UPDATE api_keys SET last_used_at = $1 WHERE key_hash = $2",
                datetime.utcnow(),
                key_hash
            )
            
            return {
                "user_id": key_record['user_id'],
                "organization_id": key_record['organization_id'],
                "scopes": key_record['scopes']
            }
            
        finally:
            await self.db_pool.release(conn)
    
    # ========================================================================
    # EMAIL SENDING HELPERS
    # ========================================================================
    
    async def send_verification_email(self, email: str, token: str):
        """Send email verification"""
        verification_url = f"https://yoursaas.com/verify-email?token={token}"
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Verify your email"
        message["From"] = settings.FROM_EMAIL
        message["To"] = email
        
        html = f"""
        <html>
            <body>
                <h2>Welcome to YourSaaS!</h2>
                <p>Please verify your email by clicking the link below:</p>
                <a href="{verification_url}">Verify Email</a>
                <p>This link will expire in 24 hours.</p>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html, "html"))
        
        await self.send_email(email, message)
    
    async def send_password_reset_email(self, email: str, token: str):
        """Send password reset email"""
        reset_url = f"https://yoursaas.com/reset-password?token={token}"
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Reset your password"
        message["From"] = settings.FROM_EMAIL
        message["To"] = email
        
        html = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Click the link below to reset your password:</p>
                <a href="{reset_url}">Reset Password</a>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html, "html"))
        
        await self.send_email(email, message)
    
    async def send_2fa_code_email(self, email: str, code: str):
        """Send 2FA code via email"""
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your verification code"
        message["From"] = settings.FROM_EMAIL
        message["To"] = email
        
        html = f"""
        <html>
            <body>
                <h2>Your Verification Code</h2>
                <p>Your verification code is:</p>
                <h1>{code}</h1>
                <p>This code will expire in {settings.TWO_FA_CODE_EXPIRE_MINUTES} minutes.</p>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html, "html"))
        
        await self.send_email(email, message)
    
    async def send_email(self, to_email: str, message: MIMEMultipart):
        """Send email using SMTP"""
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True
            )
        except Exception as e:
            self.logger.error(f"Failed to send email to {to_email}: {str(e)}")
            # Don't raise exception - email sending should not break the flow


# ============================================================================
# FASTAPI APPLICATION WITH AUTHENTICATION ENDPOINTS
# ============================================================================

app = FastAPI(title="SaaS Authentication API", version="1.0.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Initialize service
auth_service = AuthenticationService()

@app.on_event("startup")
async def startup():
    await auth_service.initialize()

@app.on_event("shutdown")
async def shutdown():
    await auth_service.close()

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    payload = await auth_service.verify_token(token)
    return payload

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest, background_tasks: BackgroundTasks):
    """Register new user"""
    return await auth_service.register_user(
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone
    )

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None
):
    """Login with email/password"""
    return await auth_service.login_user(
        email=form_data.username,
        password=form_data.password,
        ip_address=request.client.host if request else "",
        user_agent=request.headers.get("user-agent", "") if request else ""
    )

@app.post("/api/v1/auth/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: Dict = Depends(get_current_user)
):
    """Logout user"""
    await auth_service.logout_user(token, current_user['sub'])
    return {"message": "Logged out successfully"}

@app.post("/api/v1/auth/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """Refresh access token"""
    return await auth_service.refresh_access_token(data.refresh_token)

@app.post("/api/v1/auth/verify-email")
async def verify_email(token: str):
    """Verify email address"""
    await auth_service.verify_email(token)
    return {"message": "Email verified successfully"}

@app.post("/api/v1/auth/resend-verification")
async def resend_verification(email: EmailStr):
    """Resend email verification"""
    await auth_service.resend_verification_email(email)
    return {"message": "Verification email sent"}

@app.post("/api/v1/auth/password/reset-request")
async def request_password_reset(data: PasswordResetRequest):
    """Request password reset"""
    await auth_service.request_password_reset(data.email)
    return {"message": "If that email exists, reset instructions have been sent"}

@app.post("/api/v1/auth/password/reset")
async def reset_password(data: PasswordResetConfirm):
    """Reset password with token"""
    await auth_service.reset_password(data.token, data.new_password)
    return {"message": "Password reset successfully"}

@app.post("/api/v1/auth/password/change")
async def change_password(
    data: PasswordChangeRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Change password"""
    await auth_service.change_password(
        current_user['sub'],
        data.old_password,
        data.new_password
    )
    return {"message": "Password changed successfully"}

# SSO Endpoints
@app.post("/api/v1/auth/sso/initiate")
async def sso_initiate(data: SSOInitiateRequest):
    """Initiate SSO flow"""
    return await auth_service.initiate_sso(data.provider, data.redirect_uri)

@app.post("/api/v1/auth/sso/callback", response_model=TokenResponse)
async def sso_callback(data: SSOCallbackRequest, request: Request):
    """Handle SSO callback"""
    return await auth_service.handle_sso_callback(
        data.code,
        data.state,
        request.client.host,
        request.headers.get("user-agent", "")
    )

@app.get("/api/v1/auth/sso/providers")
async def list_sso_providers():
    """List available SSO providers"""
    return {
        "providers": [p.value for p in SSOProvider]
    }

@app.delete("/api/v1/auth/sso/unlink")
async def unlink_sso(current_user: Dict = Depends(get_current_user)):
    """Unlink SSO provider"""
    await auth_service.unlink_sso_provider(current_user['sub'])
    return {"message": "SSO provider unlinked"}

# 2FA Endpoints
@app.post("/api/v1/auth/2fa/enable", response_model=TwoFactorSetupResponse)
async def enable_2fa(
    data: TwoFactorEnableRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Enable 2FA"""
    return await auth_service.enable_2fa(current_user['sub'], data.password)

@app.post("/api/v1/auth/2fa/verify", response_model=TokenResponse)
async def verify_2fa(data: TwoFactorVerifyRequest, request: Request):
    """Verify 2FA code"""
    return await auth_service.verify_2fa(
        data.session_token,
        data.code,
        request.client.host,
        request.headers.get("user-agent", "")
    )

@app.post("/api/v1/auth/2fa/disable")
async def disable_2fa(
    data: TwoFactorDisableRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Disable 2FA"""
    await auth_service.disable_2fa(current_user['sub'], data.password, data.code)
    return {"message": "2FA disabled successfully"}

@app.post("/api/v1/auth/2fa/send-code")
async def send_2fa_code(session_token: str):
    """Send 2FA code via email"""
    # Get user email from session
    user_id = await auth_service.redis_client.get(f"2fa_session:{session_token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid session")
    
    conn = await auth_service.db_pool.acquire()
    try:
        user = await conn.fetchrow("SELECT email FROM users WHERE id = $1", user_id)
        return await auth_service.send_2fa_email(session_token, user['email'])
    finally:
        await auth_service.db_pool.release(conn)

@app.post("/api/v1/auth/2fa/regenerate-backup-codes")
async def regenerate_backup_codes(current_user: Dict = Depends(get_current_user)):
    """Regenerate 2FA backup codes"""
    codes = await auth_service.regenerate_backup_codes(current_user['sub'])
    return {"backup_codes": codes}

# Session Management
@app.get("/api/v1/auth/sessions")
async def list_sessions(current_user: Dict = Depends(get_current_user)):
    """List all active sessions"""
    sessions = await auth_service.get_user_sessions(current_user['sub'])
    return {"sessions": sessions}

@app.delete("/api/v1/auth/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Revoke specific session"""
    await auth_service.revoke_session(session_id, current_user['sub'])
    return {"message": "Session revoked"}

@app.delete("/api/v1/auth/sessions")
async def revoke_all_sessions(
    token: str = Depends(oauth2_scheme),
    current_user: Dict = Depends(get_current_user)
):
    """Revoke all sessions except current"""
    await auth_service.revoke_all_sessions(current_user['sub'], token)
    return {"message": "All other sessions revoked"}

# API Key Management
@app.post("/api/v1/auth/api-keys")
async def create_api_key(
    data: APIKeyCreateRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Create API key"""
    # Assume user has an organization - in real implementation, get from context
    org_id = "default-org"  # TODO: Get from user context
    
    result = await auth_service.create_api_key(
        current_user['sub'],
        org_id,
        data.name,
        data.scopes,
        data.expires_at
    )
    return result

@app.get("/api/v1/auth/api-keys")
async def list_api_keys(current_user: Dict = Depends(get_current_user)):
    """List user's API keys"""
    org_id = "default-org"  # TODO: Get from user context
    keys = await auth_service.list_api_keys(current_user['sub'], org_id)
    return {"api_keys": keys}

@app.delete("/api/v1/auth/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Revoke API key"""
    await auth_service.revoke_api_key(key_id, current_user['sub'])
    return {"message": "API key revoked"}

@app.get("/api/v1/auth/verify")
async def verify_token(current_user: Dict = Depends(get_current_user)):
    """Verify current token"""
    return {"valid": True, "user": current_user}

# Health check
@app.get("/api/v1/auth/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "authentication"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)