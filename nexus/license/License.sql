-- ============================================================================
-- Nexus Enterprise Licensing System - PostgreSQL Database Schema
-- ============================================================================
-- Version: 1.0.0
-- Database: PostgreSQL 12+
-- Author: Mauro Tommasi
-- ============================================================================

-- Create database
CREATE DATABASE nexus_licenses
    WITH 
    OWNER = nexus
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

\c nexus_licenses;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Customers table
CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255) NOT NULL UNIQUE,
    company_name VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    tax_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT check_email_format CHECK (customer_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})
);

-- Indexes for customers
CREATE INDEX idx_customers_email ON customers(customer_email);
CREATE INDEX idx_customers_company ON customers(company_name);
CREATE INDEX idx_customers_created ON customers(created_at);

-- ============================================================================
-- LICENSES TABLE
-- ============================================================================

CREATE TABLE licenses (
    license_id SERIAL PRIMARY KEY,
    license_key VARCHAR(50) NOT NULL UNIQUE,
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    
    -- License details
    license_type VARCHAR(20) NOT NULL CHECK (license_type IN ('trial', 'monthly', 'annual', 'enterprise', 'perpetual')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'suspended', 'revoked', 'pending')),
    
    -- Dates
    issue_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expiry_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Features and limits
    features JSONB NOT NULL DEFAULT '[]'::jsonb,
    max_users INTEGER NOT NULL DEFAULT 1,
    max_jobs INTEGER NOT NULL DEFAULT 10,
    max_api_calls_per_day INTEGER NOT NULL DEFAULT 1000,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Audit fields
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- Indexes for licenses
CREATE INDEX idx_licenses_key ON licenses(license_key);
CREATE INDEX idx_licenses_customer ON licenses(customer_id);
CREATE INDEX idx_licenses_status ON licenses(status);
CREATE INDEX idx_licenses_type ON licenses(license_type);
CREATE INDEX idx_licenses_expiry ON licenses(expiry_date);
CREATE INDEX idx_licenses_email ON licenses(customer_email);

-- ============================================================================
-- MACHINE ACTIVATIONS TABLE
-- ============================================================================

CREATE TABLE machine_activations (
    activation_id SERIAL PRIMARY KEY,
    license_key VARCHAR(50) NOT NULL REFERENCES licenses(license_key) ON DELETE CASCADE,
    machine_id VARCHAR(64) NOT NULL,
    activation_code VARCHAR(32) NOT NULL,
    
    -- Activation timestamps
    activated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Machine information
    hostname VARCHAR(255),
    platform VARCHAR(100),
    ip_address INET,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT unique_active_machine UNIQUE (license_key, machine_id, deactivated_at)
);

-- Indexes for machine activations
CREATE INDEX idx_activations_license ON machine_activations(license_key);
CREATE INDEX idx_activations_machine ON machine_activations(machine_id);
CREATE INDEX idx_activations_status ON machine_activations(deactivated_at) WHERE deactivated_at IS NULL;
CREATE INDEX idx_activations_last_seen ON machine_activations(last_seen_at);

-- ============================================================================
-- LICENSE ACTIVITY LOG
-- ============================================================================

CREATE TABLE license_activity (
    activity_id BIGSERIAL PRIMARY KEY,
    license_key VARCHAR(50) NOT NULL REFERENCES licenses(license_key) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_details JSONB,
    activity_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    
    -- Partitioning by month
    PARTITION BY RANGE (activity_timestamp)
);

-- Create partitions for activity log (example for 2024-2025)
CREATE TABLE license_activity_2024_q4 PARTITION OF license_activity
    FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');

CREATE TABLE license_activity_2025_q1 PARTITION OF license_activity
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');

CREATE TABLE license_activity_2025_q2 PARTITION OF license_activity
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');

CREATE TABLE license_activity_2025_q3 PARTITION OF license_activity
    FOR VALUES FROM ('2025-07-01') TO ('2025-10-01');

CREATE TABLE license_activity_2025_q4 PARTITION OF license_activity
    FOR VALUES FROM ('2025-10-01') TO ('2026-01-01');

-- Indexes for activity log
CREATE INDEX idx_activity_license ON license_activity(license_key);
CREATE INDEX idx_activity_type ON license_activity(activity_type);
CREATE INDEX idx_activity_timestamp ON license_activity(activity_timestamp);

-- ============================================================================
-- API USAGE TRACKING
-- ============================================================================

CREATE TABLE api_usage (
    usage_id BIGSERIAL PRIMARY KEY,
    license_key VARCHAR(50) NOT NULL REFERENCES licenses(license_key) ON DELETE CASCADE,
    call_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    response_code INTEGER,
    response_time_ms INTEGER,
    ip_address INET,
    user_agent TEXT,
    
    -- Partitioning by month
    PARTITION BY RANGE (call_timestamp)
);

-- Create partitions for API usage
CREATE TABLE api_usage_2024_q4 PARTITION OF api_usage
    FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');

CREATE TABLE api_usage_2025_q1 PARTITION OF api_usage
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');

CREATE TABLE api_usage_2025_q2 PARTITION OF api_usage
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');

CREATE TABLE api_usage_2025_q3 PARTITION OF api_usage
    FOR VALUES FROM ('2025-07-01') TO ('2025-10-01');

CREATE TABLE api_usage_2025_q4 PARTITION OF api_usage
    FOR VALUES FROM ('2025-10-01') TO ('2026-01-01');

-- Indexes for API usage
CREATE INDEX idx_api_usage_license ON api_usage(license_key);
CREATE INDEX idx_api_usage_timestamp ON api_usage(call_timestamp);
CREATE INDEX idx_api_usage_endpoint ON api_usage(endpoint);

-- ============================================================================
-- SUBSCRIPTIONS TABLE
-- ============================================================================

CREATE TABLE subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    license_key VARCHAR(50) NOT NULL REFERENCES licenses(license_key) ON DELETE CASCADE,
    
    -- Subscription details
    plan_name VARCHAR(100) NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL CHECK (billing_cycle IN ('monthly', 'annual', 'one-time')),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'past_due', 'expired')),
    
    -- Dates
    start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    next_billing_date TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    -- Payment information
    payment_method VARCHAR(50),
    payment_provider VARCHAR(50),
    payment_provider_id VARCHAR(255),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for subscriptions
CREATE INDEX idx_subscriptions_customer ON subscriptions(customer_id);
CREATE INDEX idx_subscriptions_license ON subscriptions(license_key);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_next_billing ON subscriptions(next_billing_date);

-- ============================================================================
-- PAYMENTS TABLE
-- ============================================================================

CREATE TABLE payments (
    payment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID REFERENCES subscriptions(subscription_id) ON DELETE SET NULL,
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    license_key VARCHAR(50) REFERENCES licenses(license_key) ON DELETE SET NULL,
    
    -- Payment details
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    
    -- Payment method
    payment_method VARCHAR(50),
    payment_provider VARCHAR(50),
    payment_provider_id VARCHAR(255),
    transaction_id VARCHAR(255),
    
    -- Dates
    payment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    invoice_number VARCHAR(50),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for payments
CREATE INDEX idx_payments_customer ON payments(customer_id);
CREATE INDEX idx_payments_subscription ON payments(subscription_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_date ON payments(payment_date);
CREATE INDEX idx_payments_invoice ON payments(invoice_number);

-- ============================================================================
-- LICENSE FEATURES TABLE
-- ============================================================================

CREATE TABLE license_features (
    feature_id SERIAL PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL UNIQUE,
    feature_description TEXT,
    feature_category VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default features
INSERT INTO license_features (feature_name, feature_description, feature_category) VALUES
    ('basic_etl', 'Basic ETL Operations', 'etl'),
    ('advanced_etl', 'Advanced ETL with Custom Code', 'etl'),
    ('database_management', 'Database Management Tools', 'database'),
    ('pipeline_automation', 'Pipeline Automation and Scheduling', 'automation'),
    ('api_access', 'REST API Access', 'api'),
    ('cloud_connectors', 'Cloud Storage Connectors (S3, Azure, GCS)', 'cloud'),
    ('custom_code', 'Custom Python Code Execution', 'development'),
    ('enterprise_support', '24/7 Enterprise Support', 'support'),
    ('unlimited_jobs', 'Unlimited Job Execution', 'limits'),
    ('priority_support', 'Priority Support Queue', 'support');

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Active licenses view
CREATE VIEW v_active_licenses AS
SELECT 
    l.*,
    c.company_name,
    c.phone,
    c.country,
    COUNT(DISTINCT ma.machine_id) FILTER (WHERE ma.deactivated_at IS NULL) as active_machines,
    l.expiry_date - CURRENT_TIMESTAMP as time_until_expiry
FROM licenses l
JOIN customers c ON l.customer_id = c.customer_id
LEFT JOIN machine_activations ma ON l.license_key = ma.license_key
WHERE l.status = 'active'
AND l.expiry_date > CURRENT_TIMESTAMP
GROUP BY l.license_id, c.customer_id;

-- License usage summary view
CREATE VIEW v_license_usage_summary AS
SELECT 
    l.license_key,
    l.customer_name,
    l.license_type,
    l.status,
    COUNT(DISTINCT ma.machine_id) FILTER (WHERE ma.deactivated_at IS NULL) as active_machines,
    l.max_users,
    COUNT(au.usage_id) FILTER (WHERE au.call_timestamp >= CURRENT_DATE) as api_calls_today,
    l.max_api_calls_per_day,
    l.expiry_date,
    EXTRACT(EPOCH FROM (l.expiry_date - CURRENT_TIMESTAMP))/86400 as days_until_expiry
FROM licenses l
LEFT JOIN machine_activations ma ON l.license_key = ma.license_key
LEFT JOIN api_usage au ON l.license_key = au.license_key
GROUP BY l.license_key, l.customer_name, l.license_type, l.status, l.max_users, l.max_api_calls_per_day, l.expiry_date;

-- Expiring licenses view (next 30 days)
CREATE VIEW v_expiring_licenses AS
SELECT 
    l.license_key,
    l.customer_name,
    l.customer_email,
    l.license_type,
    l.expiry_date,
    EXTRACT(EPOCH FROM (l.expiry_date - CURRENT_TIMESTAMP))/86400 as days_until_expiry,
    s.subscription_id,
    s.next_billing_date
FROM licenses l
LEFT JOIN subscriptions s ON l.license_key = s.license_key AND s.status = 'active'
WHERE l.status = 'active'
AND l.expiry_date BETWEEN CURRENT_TIMESTAMP AND CURRENT_TIMESTAMP + INTERVAL '30 days'
ORDER BY l.expiry_date;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Apply trigger to relevant tables
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_licenses_updated_at BEFORE UPDATE ON licenses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to check and update expired licenses
CREATE OR REPLACE FUNCTION check_expired_licenses()
RETURNS void AS $
BEGIN
    UPDATE licenses
    SET status = 'expired'
    WHERE status = 'active'
    AND expiry_date < CURRENT_TIMESTAMP;
END;
$ LANGUAGE plpgsql;

-- Function to get license statistics
CREATE OR REPLACE FUNCTION get_license_stats()
RETURNS TABLE (
    total_licenses BIGINT,
    active_licenses BIGINT,
    expired_licenses BIGINT,
    trial_licenses BIGINT,
    paid_licenses BIGINT,
    total_revenue DECIMAL
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_licenses,
        COUNT(*) FILTER (WHERE status = 'active')::BIGINT as active_licenses,
        COUNT(*) FILTER (WHERE status = 'expired')::BIGINT as expired_licenses,
        COUNT(*) FILTER (WHERE license_type = 'trial')::BIGINT as trial_licenses,
        COUNT(*) FILTER (WHERE license_type IN ('monthly', 'annual', 'enterprise'))::BIGINT as paid_licenses,
        COALESCE(SUM(p.amount), 0) as total_revenue
    FROM licenses l
    LEFT JOIN payments p ON l.license_key = p.license_key AND p.status = 'completed';
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- SCHEDULED JOBS (using pg_cron extension - optional)
-- ============================================================================

-- If pg_cron is installed:
-- CREATE EXTENSION pg_cron;

-- Schedule daily check for expired licenses (run at 1 AM)
-- SELECT cron.schedule('check-expired-licenses', '0 1 * * *', 'SELECT check_expired_licenses()');

-- ============================================================================
-- SECURITY & PERMISSIONS
-- ============================================================================

-- Create role for application
CREATE ROLE nexus_app WITH LOGIN PASSWORD 'change_me_in_production';

-- Grant permissions
GRANT CONNECT ON DATABASE nexus_licenses TO nexus_app;
GRANT USAGE ON SCHEMA public TO nexus_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO nexus_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nexus_app;

-- Create read-only role for reporting
CREATE ROLE nexus_readonly WITH LOGIN PASSWORD 'change_me_readonly';
GRANT CONNECT ON DATABASE nexus_licenses TO nexus_readonly;
GRANT USAGE ON SCHEMA public TO nexus_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nexus_readonly;

-- Row-level security example (optional)
-- ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY license_isolation ON licenses
--     USING (customer_email = current_user);

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

-- Insert sample customer
INSERT INTO customers (customer_id, customer_name, customer_email, company_name, country)
VALUES 
    ('123e4567-e89b-12d3-a456-426614174000', 'John Doe', 'john.doe@example.com', 'Example Corp', 'USA');

-- Insert sample license
INSERT INTO licenses (
    license_key, customer_id, customer_name, customer_email, 
    license_type, status, issue_date, expiry_date,
    features, max_users, max_jobs
) VALUES (
    'NEXUS-ABCD-EFGH-IJKL-MNOP',
    '123e4567-e89b-12d3-a456-426614174000',
    'John Doe',
    'john.doe@example.com',
    'annual',
    'active',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '365 days',
    '["basic_etl", "advanced_etl", "database_management", "api_access"]'::jsonb,
    5,
    100
);

-- ============================================================================
-- MAINTENANCE QUERIES
-- ============================================================================

-- Clean up old activity logs (older than 1 year)
-- DELETE FROM license_activity WHERE activity_timestamp < CURRENT_TIMESTAMP - INTERVAL '1 year';

-- Clean up old API usage data (older than 90 days)
-- DELETE FROM api_usage WHERE call_timestamp < CURRENT_TIMESTAMP - INTERVAL '90 days';

-- Vacuum and analyze
-- VACUUM ANALYZE;

-- ============================================================================
-- BACKUP RECOMMENDATIONS
-- ============================================================================

-- Daily full backup:
-- pg_dump -h localhost -U nexus -d nexus_licenses -F c -f nexus_licenses_$(date +%Y%m%d).backup

-- Point-in-time recovery setup:
-- Enable WAL archiving in postgresql.conf:
-- wal_level = replica
-- archive_mode = on
-- archive_command = 'cp %p /backup/archive/%f'