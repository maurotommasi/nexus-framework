-- Production-Ready Database Schema for Authentication System
-- PostgreSQL 14+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table with proper constraints and indexes
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- Nullable for SSO-only users
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    avatar_url TEXT,
    
    -- Two-factor authentication
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(32),
    backup_codes TEXT[],  -- Array of hashed backup codes
    
    -- SSO
    sso_provider VARCHAR(50),
    sso_provider_id VARCHAR(255),
    
    -- Status and verification
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
    email_verified BOOLEAN DEFAULT FALSE,
    tier VARCHAR(20) DEFAULT 'free' CHECK (tier IN ('free', 'normal', 'pro', 'enterprise')),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT email_lowercase CHECK (email = LOWER(email)),
    CONSTRAINT sso_or_password CHECK (
        (password_hash IS NOT NULL) OR 
        (sso_provider IS NOT NULL AND sso_provider_id IS NOT NULL)
    )
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_sso ON users(sso_provider, sso_provider_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_status ON users(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Email verification tokens
CREATE TABLE email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT token_not_used CHECK (used_at IS NULL OR used_at <= CURRENT_TIMESTAMP)
);

CREATE INDEX idx_email_tokens_token ON email_verification_tokens(token) WHERE used_at IS NULL;
CREATE INDEX idx_email_tokens_user ON email_verification_tokens(user_id);
CREATE INDEX idx_email_tokens_expires ON email_verification_tokens(expires_at) WHERE used_at IS NULL;

-- Password reset tokens
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    
    CONSTRAINT reset_token_not_used CHECK (used_at IS NULL OR used_at <= CURRENT_TIMESTAMP)
);

CREATE INDEX idx_reset_tokens_token ON password_reset_tokens(token) WHERE used_at IS NULL;
CREATE INDEX idx_reset_tokens_user ON password_reset_tokens(user_id);
CREATE INDEX idx_reset_tokens_expires ON password_reset_tokens(expires_at) WHERE used_at IS NULL;

-- User sessions
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,  -- Access token (for revocation)
    refresh_token TEXT NOT NULL,
    jti VARCHAR(255),  -- JWT ID for precise revocation
    
    -- Session metadata
    ip_address INET NOT NULL,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id) WHERE revoked_at IS NULL AND expires_at > CURRENT_TIMESTAMP;
CREATE INDEX idx_sessions_jti ON user_sessions(jti) WHERE revoked_at IS NULL;
CREATE INDEX idx_sessions_refresh ON user_sessions(refresh_token) WHERE revoked_at IS NULL;
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at) WHERE revoked_at IS NULL;

-- API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID,  -- For multi-tenant support
    
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 hash
    key_prefix VARCHAR(20) NOT NULL,  -- First 12 chars for identification
    
    scopes TEXT[] NOT NULL DEFAULT '{}',  -- Array of permission scopes
    
    -- Status and usage
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count BIGINT DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash) WHERE is_active = TRUE AND revoked_at IS NULL;
CREATE INDEX idx_api_keys_user ON api_keys(user_id) WHERE is_active = TRUE;
CREATE INDEX idx_api_keys_org ON api_keys(organization_id) WHERE is_active = TRUE;
CREATE INDEX idx_api_keys_expires ON api_keys(expires_at) WHERE is_active = TRUE AND revoked_at IS NULL;

-- Audit logs for security events
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,  -- 'login', 'logout', 'password_change', etc.
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Request metadata
    ip_address INET NOT NULL,
    user_agent TEXT,
    
    -- Event details
    metadata JSONB,  -- Flexible storage for event-specific data
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit log queries
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_event ON audit_logs(event_type, created_at DESC);
CREATE INDEX idx_audit_logs_ip ON audit_logs(ip_address, created_at DESC);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_failed ON audit_logs(success, created_at DESC) WHERE success = FALSE;

-- Metadata index for specific queries
CREATE INDEX idx_audit_logs_metadata ON audit_logs USING gin(metadata);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Cleanup function for expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    -- Delete expired email verification tokens
    DELETE FROM email_verification_tokens
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
    
    -- Delete expired password reset tokens
    DELETE FROM password_reset_tokens
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
    
    -- Delete expired sessions
    DELETE FROM user_sessions
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    -- Optionally delete old audit logs (keep last 90 days)
    DELETE FROM audit_logs
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-expired-tokens', '0 2 * * *', 'SELECT cleanup_expired_tokens()');

-- Organizations table (for multi-tenancy)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    
    -- Plan and limits
    plan VARCHAR(50) DEFAULT 'free',
    max_users INTEGER,
    max_api_keys INTEGER,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_organizations_slug ON organizations(slug) WHERE deleted_at IS NULL;

-- Organization memberships
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    role VARCHAR(50) NOT NULL DEFAULT 'member',  -- owner, admin, member
    
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(organization_id, user_id)
);

CREATE INDEX idx_org_members_org ON organization_members(organization_id);
CREATE INDEX idx_org_members_user ON organization_members(user_id);

-- Permissions table (for fine-grained access control)
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource VARCHAR(100) NOT NULL,  -- 'users', 'api_keys', etc.
    action VARCHAR(50) NOT NULL,  -- 'read', 'write', 'delete'
    
    UNIQUE(resource, action)
);

-- Role permissions (RBAC)
CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role VARCHAR(50) NOT NULL,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    
    UNIQUE(role, permission_id)
);

-- Insert default permissions
INSERT INTO permissions (resource, action) VALUES
    ('users', 'read'),
    ('users', 'write'),
    ('users', 'delete'),
    ('api_keys', 'read'),
    ('api_keys', 'write'),
    ('api_keys', 'delete'),
    ('sessions', 'read'),
    ('sessions', 'delete'),
    ('audit_logs', 'read');

-- Create read-only user for reporting (optional)
CREATE USER auth_readonly WITH PASSWORD 'secure_password_here';
GRANT CONNECT ON DATABASE saas_db TO auth_readonly;
GRANT USAGE ON SCHEMA public TO auth_readonly;
GRANT SELECT ON audit_logs, users, user_sessions TO auth_readonly;

-- Row-level security example (for multi-tenancy)
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY api_keys_isolation ON api_keys
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

-- Views for common queries
CREATE OR REPLACE VIEW active_users AS
SELECT 
    id, email, first_name, last_name,
    tier, created_at, last_login_at
FROM users
WHERE status = 'active' AND deleted_at IS NULL;

CREATE OR REPLACE VIEW recent_login_attempts AS
SELECT 
    event_type,
    user_id,
    ip_address,
    success,
    metadata,
    created_at
FROM audit_logs
WHERE event_type IN ('login_failed', 'user_login')
    AND created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Materialized view for analytics (refresh periodically)
CREATE MATERIALIZED VIEW user_statistics AS
SELECT 
    tier,
    COUNT(*) as total_users,
    COUNT(CASE WHEN email_verified THEN 1 END) as verified_users,
    COUNT(CASE WHEN two_factor_enabled THEN 1 END) as users_with_2fa,
    COUNT(CASE WHEN sso_provider IS NOT NULL THEN 1 END) as sso_users,
    COUNT(CASE WHEN last_login_at > CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 1 END) as active_users
FROM users
WHERE status = 'active' AND deleted_at IS NULL
GROUP BY tier;

CREATE UNIQUE INDEX ON user_statistics (tier);

-- Refresh materialized view (run periodically)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY user_statistics;