"""
Production-Ready Authentication & Authorization System for SaaS Platform
File: auth_service.py

Key Improvements:
- Environment variable configuration
- Proper error handling and logging
- Rate limiting with sliding window
- SQL injection prevention
- Input sanitization
- Secure session management
- Audit logging
- CORS configuration
- Health checks with dependencies
"""

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, EmailStr, Field, validator, SecretStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
import pyotp
import qrcode
import io
import base64
import redis.asyncio as redis
import asyncpg
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import hashlib
from enum import Enum
import uuid
import httpx
import logging
import os
from functools import wraps
import time
from contextlib import asynccontextmanager

# ============================================================================
# CONFIGURATION - Use Environment Variables
# ============================================================================

class Settings:
    # JWT Settings
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_MIN_SIZE = int(os.getenv("DB_MIN_SIZE", "10"))
    DB_MAX_SIZE = int(os.getenv("DB_MAX_SIZE", "20"))
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL")
    
    # Email
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    FROM_EMAIL = os.getenv("FROM_EMAIL")
    
    # SSO
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    
    # 2FA
    TOTP_ISSUER = os.getenv("TOTP_ISSUER", "YourSaaS")
    TWO_FA_CODE_EXPIRE_MINUTES = 5
    
    # Security
    PASSWORD_MIN_LENGTH = 12
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    def validate(self):
        """Validate required settings"""
        required = [
            "SECRET_KEY", "DATABASE_URL", "REDIS_URL",
            "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"
        ]
        missing = [key for key in required if not getattr(self, key)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")

settings = Settings()
settings.validate()

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# SECURITY UTILITIES
# ============================================================================

class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 255) -> str:
        """Sanitize user input"""
        if not text:
            return ""
        # Remove null bytes and limit length
        return text.replace('\x00', '').strip()[:max_length]
    
    @staticmethod
    def is_safe_redirect(url: str) -> bool:
        """Check if redirect URL is safe"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        # Only allow same domain redirects or whitelisted domains
        return parsed.netloc in settings.ALLOWED_HOSTS or not parsed.netloc

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Token bucket rate limiter with Redis"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_rate_limit(
        self, 
        key: str, 
        max_requests: int = None, 
        window: int = None
    ) -> bool:
        """Check if request is within rate limit"""
        max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        window = window or settings.RATE_LIMIT_WINDOW
        
        current = int(time.time())
        window_start = current - window
        
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Add current request
        pipe.zadd(key, {str(current): current})
        # Count requests in window
        pipe.zcard(key)
        # Set expiry
        pipe.expire(key, window)
        
        results = await pipe.execute()
        request_count = results[2]
        
        return request_count <= max_requests

# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """Audit logger for security events"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.logger = logging.getLogger("audit")
    
    async def log_event(
        self,
        event_type: str,
        user_id: Optional[str],
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict] = None,
        success: bool = True
    ):
        """Log security audit event"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_logs 
                    (event_type, user_id, ip_address, user_agent, metadata, success)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    event_type,
                    user_id,
                    ip_address,
                    user_agent,
                    metadata,
                    success
                )
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")

# ============================================================================
# PYDANTIC MODELS (with improved validation)
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

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(..., min_length=12)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    @validator('password')
    def validate_password(cls, v):
        password = v.get_secret_value() if hasattr(v, 'get_secret_value') else v
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {settings.PASSWORD_MIN_LENGTH} characters')
        if not any(char.isdigit() for char in password):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in password):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in password):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in password):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        return SecurityUtils.sanitize_input(v, 100)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

# ============================================================================
# AUTHENTICATION SERVICE CLASS
# ============================================================================

class AuthenticationService:
    """Production-ready Authentication & Authorization Service"""
    
    def __init__(self):
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12  # Increase rounds for better security
        )
        self.redis_client = None
        self.db_pool = None
        self.rate_limiter = None
        self.audit_logger = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize connections with proper error handling"""
        try:
            # Initialize Redis with retry
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            await self.redis_client.ping()
            
            # Initialize PostgreSQL pool
            self.db_pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=settings.DB_MIN_SIZE,
                max_size=settings.DB_MAX_SIZE,
                command_timeout=60
            )
            
            # Initialize utilities
            self.rate_limiter = RateLimiter(self.redis_client)
            self.audit_logger = AuditLogger(self.db_pool)
            
            self.logger.info("Auth service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize auth service: {e}")
            raise
    
    async def close(self):
        """Gracefully close connections"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            if self.db_pool:
                await self.db_pool.close()
            self.logger.info("Auth service closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing connections: {e}")
    
    async def check_request_rate_limit(self, key: str, max_requests: int = None):
        """Check rate limit and raise exception if exceeded"""
        if not await self.rate_limiter.check_rate_limit(key, max_requests):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
    
    def hash_password(self, password: str) -> str:
        """Hash password with timing attack protection"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password with constant-time comparison"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT with additional security claims"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # JWT ID for tracking
        })
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    def create_refresh_token(self, data: dict) -> str:
        """Create refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        })
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT with comprehensive checks"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={
                    "verify_exp": True,
                    "verify_iat": True,
                    "require_exp": True
                }
            )
            
            # Check blacklist
            jti = payload.get("jti")
            if jti:
                is_blacklisted = await self.redis_client.get(f"blacklist:{jti}")
                if is_blacklisted:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has been revoked"
                    )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except JWTError as e:
            self.logger.warning(f"Token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str],
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """Register user with comprehensive validation"""
        
        # Rate limit registration
        await self.check_request_rate_limit(f"register:{ip_address}", max_requests=5)
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Check existing user
                existing = await conn.fetchrow(
                    "SELECT id FROM users WHERE email = $1",
                    email.lower()
                )
                
                if existing:
                    # Audit failed attempt
                    await self.audit_logger.log_event(
                        "registration_failed",
                        None,
                        ip_address,
                        user_agent,
                        {"reason": "email_exists"},
                        success=False
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
                
                # Create user
                user_id = str(uuid.uuid4())
                hashed_password = self.hash_password(password)
                
                await conn.execute(
                    """
                    INSERT INTO users (
                        id, email, password_hash, first_name, last_name,
                        phone, status, email_verified, tier, created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    user_id,
                    email.lower(),
                    hashed_password,
                    SecurityUtils.sanitize_input(first_name),
                    SecurityUtils.sanitize_input(last_name),
                    phone,
                    UserStatus.ACTIVE.value,
                    False,
                    UserTier.FREE.value,
                    datetime.utcnow()
                )
                
                # Generate verification token
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
                
                # Audit successful registration
                await self.audit_logger.log_event(
                    "user_registered",
                    user_id,
                    ip_address,
                    user_agent
                )
                
                # Send verification email (non-blocking)
                try:
                    await self.send_verification_email(email, verification_token)
                except Exception as e:
                    self.logger.error(f"Failed to send verification email: {e}")
                
                return {
                    "user_id": user_id,
                    "email": email,
                    "message": "Registration successful. Please verify your email."
                }
    
    async def login_user(
        self,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """Secure login with rate limiting"""
        
        # Rate limit login attempts
        await self.check_request_rate_limit(f"login:{ip_address}", max_requests=10)
        
        attempts_key = f"login_attempts:{email.lower()}"
        attempts = await self.redis_client.get(attempts_key)
        
        if attempts and int(attempts) >= settings.MAX_LOGIN_ATTEMPTS:
            await self.audit_logger.log_event(
                "login_failed",
                None,
                ip_address,
                user_agent,
                {"reason": "account_locked"},
                success=False
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account temporarily locked. Try again in {settings.LOCKOUT_DURATION_MINUTES} minutes."
            )
        
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                """
                SELECT id, email, password_hash, two_factor_enabled,
                       status, tier, email_verified
                FROM users
                WHERE email = $1
                """,
                email.lower()
            )
            
            if not user or not self.verify_password(password, user['password_hash']):
                # Increment attempts
                await self.redis_client.incr(attempts_key)
                await self.redis_client.expire(
                    attempts_key,
                    settings.LOCKOUT_DURATION_MINUTES * 60
                )
                
                await self.audit_logger.log_event(
                    "login_failed",
                    user['id'] if user else None,
                    ip_address,
                    user_agent,
                    {"reason": "invalid_credentials"},
                    success=False
                )
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Verify account status
            if user['status'] != UserStatus.ACTIVE.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is not active"
                )
            
            if not user['email_verified']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Please verify your email first"
                )
            
            # Clear login attempts
            await self.redis_client.delete(attempts_key)
            
            # Handle 2FA
            if user['two_factor_enabled']:
                session_token = secrets.token_urlsafe(32)
                await self.redis_client.setex(
                    f"2fa_session:{session_token}",
                    600,
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
            refresh_token = self.create_refresh_token(data={"sub": user['id']})
            
            # Create session
            await self.create_session(
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
            
            # Audit successful login
            await self.audit_logger.log_event(
                "user_login",
                user['id'],
                ip_address,
                user_agent
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
    
    async def create_session(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        ip_address: str,
        user_agent: str
    ) -> str:
        """Create secure session"""
        async with self.db_pool.acquire() as conn:
            session_id = str(uuid.uuid4())
            
            # Extract JTI for token tracking
            payload = jwt.decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            jti = payload.get("jti")
            
            await conn.execute(
                """
                INSERT INTO user_sessions (
                    id, user_id, token, refresh_token, jti,
                    ip_address, user_agent, expires_at, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                session_id,
                user_id,
                access_token,
                refresh_token,
                jti,
                ip_address,
                user_agent,
                datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                datetime.utcnow()
            )
            
            return session_id
    
    async def send_verification_email(self, email: str, token: str):
        """Send verification email with proper error handling"""
        try:
            verification_url = f"https://yoursaas.com/verify-email?token={token}"
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Verify your email"
            message["From"] = settings.FROM_EMAIL
            message["To"] = email
            
            html = f"""
            <html>
                <body>
                    <h2>Welcome!</h2>
                    <p>Please verify your email:</p>
                    <a href="{verification_url}">Verify Email</a>
                    <p>Expires in 24 hours.</p>
                </body>
            </html>
            """
            
            message.attach(MIMEText(html, "html"))
            
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True,
                timeout=10
            )
            
        except Exception as e:
            self.logger.error(f"Email send failed: {e}")
            # Don't raise - email failure shouldn't block registration


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    await auth_service.initialize()
    yield
    # Shutdown
    await auth_service.close()

app = FastAPI(
    title="SaaS Authentication API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)

if settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
auth_service = AuthenticationService()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Get current authenticated user"""
    return await auth_service.verify_token(token)

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest, request: Request):
    """Register new user"""
    return await auth_service.register_user(
        email=data.email,
        password=data.password.get_secret_value(),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "")
    )

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None
):
    """User login"""
    return await auth_service.login_user(
        email=form_data.username,
        password=form_data.password,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "")
    )

@app.get("/api/v1/auth/health")
async def health_check():
    """Comprehensive health check"""
    health = {
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Check Redis
        await auth_service.redis_client.ping()
        health["redis"] = "healthy"
    except Exception as e:
        health["redis"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"
    
    try:
        # Check Database
        async with auth_service.db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        health["database"] = "healthy"
    except Exception as e:
        health["database"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"
    
    return health

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True
    )