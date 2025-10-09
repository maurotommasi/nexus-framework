-- ============================================================================
-- POSTGRESQL SCHEMA FOR SECURE BLOCKCHAIN MANAGER
-- Each user has their own database with encrypted name based on email
-- ============================================================================

-- ============================================================================
-- MASTER DATABASE SETUP (postgres or main database)
-- This tracks all user databases
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_databases (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) UNIQUE NOT NULL,
    database_name VARCHAR(255) UNIQUE NOT NULL, -- Encrypted email hash
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    database_size_mb DECIMAL(10, 2),
    
    CONSTRAINT email_format CHECK (user_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_user_databases_email ON user_databases(user_email);
CREATE INDEX idx_user_databases_dbname ON user_databases(database_name);
CREATE INDEX idx_user_databases_active ON user_databases(is_active) WHERE is_active = TRUE;

-- ============================================================================
-- FUNCTIONS FOR DATABASE MANAGEMENT
-- ============================================================================

-- Function to generate encrypted database name from email
CREATE OR REPLACE FUNCTION generate_database_name(p_email VARCHAR)
RETURNS VARCHAR AS $$
DECLARE
    v_hash VARCHAR;
BEGIN
    -- Create SHA256 hash of email and take first 32 chars
    v_hash := encode(digest(lower(p_email), 'sha256'), 'hex');
    -- Prefix with 'user_db_' to make it identifiable
    RETURN 'user_db_' || substring(v_hash, 1, 32);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to create user database
CREATE OR REPLACE FUNCTION create_user_database(p_email VARCHAR)
RETURNS VARCHAR AS $$
DECLARE
    v_db_name VARCHAR;
    v_exists BOOLEAN;
BEGIN
    -- Generate database name
    v_db_name := generate_database_name(p_email);
    
    -- Check if database already exists
    SELECT EXISTS(
        SELECT 1 FROM pg_database WHERE datname = v_db_name
    ) INTO v_exists;
    
    IF v_exists THEN
        RAISE EXCEPTION 'Database for email % already exists', p_email;
    END IF;
    
    -- Create database
    EXECUTE format('CREATE DATABASE %I', v_db_name);
    
    -- Insert record
    INSERT INTO user_databases (user_email, database_name)
    VALUES (p_email, v_db_name);
    
    RETURN v_db_name;
END;
$$ LANGUAGE plpgsql;

-- Function to get database name for user
CREATE OR REPLACE FUNCTION get_user_database(p_email VARCHAR)
RETURNS VARCHAR AS $$
DECLARE
    v_db_name VARCHAR;
BEGIN
    SELECT database_name INTO v_db_name
    FROM user_databases
    WHERE user_email = p_email AND is_active = TRUE;
    
    RETURN v_db_name;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- USER DATABASE SCHEMA (To be created in each user's database)
-- Run this script after connecting to the user's database
-- ============================================================================

-- ============================================================================
-- TABLE: users
-- Stores user account information
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, -- bcrypt hash
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret TEXT,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- ============================================================================
-- TABLE: wallets
-- Stores encrypted wallet information
-- ============================================================================

CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address VARCHAR(42) UNIQUE NOT NULL, -- Ethereum address
    encrypted_keystore JSONB NOT NULL, -- Encrypted private key
    keystore_type VARCHAR(50) DEFAULT 'encrypted', -- encrypted, web3, hardware, kms
    chain_type VARCHAR(50) NOT NULL, -- ethereum, polygon, bitcoin, solana
    is_primary BOOLEAN DEFAULT FALSE,
    label VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    
    CONSTRAINT eth_address_format CHECK (address ~* '^0x[a-fA-F0-9]{40}$')
);

CREATE INDEX idx_wallets_user ON wallets(user_id);
CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_wallets_chain ON wallets(chain_type);
CREATE INDEX idx_wallets_primary ON wallets(user_id, is_primary) WHERE is_primary = TRUE;

-- ============================================================================
-- TABLE: transactions
-- Stores transaction history
-- ============================================================================

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id INTEGER REFERENCES wallets(id) ON DELETE SET NULL,
    tx_hash VARCHAR(66) UNIQUE NOT NULL,
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    amount DECIMAL(36, 18) NOT NULL, -- Supports up to 18 decimals
    chain_type VARCHAR(50) NOT NULL,
    token_standard VARCHAR(20), -- native, erc20, erc721, erc1155
    token_address VARCHAR(42), -- For token transfers
    token_id BIGINT, -- For NFTs
    status VARCHAR(20) DEFAULT 'pending', -- pending, confirmed, failed
    block_number BIGINT,
    gas_used BIGINT,
    gas_price BIGINT,
    gas_cost DECIMAL(36, 18),
    nonce INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    
    CONSTRAINT status_values CHECK (status IN ('pending', 'sent', 'confirmed', 'failed'))
);

CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_wallet ON transactions(wallet_id);
CREATE INDEX idx_transactions_hash ON transactions(tx_hash);
CREATE INDEX idx_transactions_from ON transactions(from_address);
CREATE INDEX idx_transactions_to ON transactions(to_address);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created ON transactions(created_at DESC);
CREATE INDEX idx_transactions_chain ON transactions(chain_type);

-- ============================================================================
-- TABLE: smart_contracts
-- Stores deployed smart contracts
-- ============================================================================

CREATE TABLE IF NOT EXISTS smart_contracts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address VARCHAR(42) UNIQUE NOT NULL,
    name VARCHAR(255),
    abi JSONB NOT NULL,
    bytecode TEXT,
    chain_type VARCHAR(50) NOT NULL,
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deploy_tx_hash VARCHAR(66),
    contract_type VARCHAR(50), -- erc20, erc721, erc1155, custom
    is_verified BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT eth_address_format CHECK (address ~* '^0x[a-fA-F0-9]{40}$')
);

CREATE INDEX idx_contracts_user ON smart_contracts(user_id);
CREATE INDEX idx_contracts_address ON smart_contracts(address);
CREATE INDEX idx_contracts_chain ON smart_contracts(chain_type);
CREATE INDEX idx_contracts_type ON smart_contracts(contract_type);

-- ============================================================================
-- TABLE: multi_sig_wallets
-- Stores multi-signature wallet configurations
-- ============================================================================

CREATE TABLE IF NOT EXISTS multi_sig_wallets (
    id SERIAL PRIMARY KEY,
    address VARCHAR(42) UNIQUE NOT NULL,
    name VARCHAR(255),
    required_signatures INTEGER NOT NULL,
    chain_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT required_sigs_positive CHECK (required_signatures > 0),
    CONSTRAINT eth_address_format CHECK (address ~* '^0x[a-fA-F0-9]{40}$')
);

CREATE INDEX idx_multisig_address ON multi_sig_wallets(address);
CREATE INDEX idx_multisig_active ON multi_sig_wallets(is_active) WHERE is_active = TRUE;

-- ============================================================================
-- TABLE: multi_sig_owners
-- Stores owners of multi-signature wallets
-- ============================================================================

CREATE TABLE IF NOT EXISTS multi_sig_owners (
    id SERIAL PRIMARY KEY,
    multi_sig_id INTEGER NOT NULL REFERENCES multi_sig_wallets(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    wallet_id INTEGER REFERENCES wallets(id) ON DELETE CASCADE,
    owner_address VARCHAR(42) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT unique_multisig_owner UNIQUE (multi_sig_id, owner_address),
    CONSTRAINT eth_address_format CHECK (owner_address ~* '^0x[a-fA-F0-9]{40}$')
);

CREATE INDEX idx_multisig_owners_wallet ON multi_sig_owners(multi_sig_id);
CREATE INDEX idx_multisig_owners_user ON multi_sig_owners(user_id);
CREATE INDEX idx_multisig_owners_address ON multi_sig_owners(owner_address);

-- ============================================================================
-- TABLE: multi_sig_transactions
-- Stores multi-sig pending and executed transactions
-- ============================================================================

CREATE TABLE IF NOT EXISTS multi_sig_transactions (
    id SERIAL PRIMARY KEY,
    multi_sig_id INTEGER NOT NULL REFERENCES multi_sig_wallets(id) ON DELETE CASCADE,
    tx_id VARCHAR(32) UNIQUE NOT NULL, -- Internal transaction ID
    proposer_id INTEGER REFERENCES users(id),
    proposer_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    amount DECIMAL(36, 18) NOT NULL,
    data TEXT, -- For contract interactions
    status VARCHAR(20) DEFAULT 'pending', -- pending, executed, cancelled
    proposed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    executed_by INTEGER REFERENCES users(id),
    tx_hash VARCHAR(66), -- Blockchain transaction hash
    
    CONSTRAINT status_values CHECK (status IN ('pending', 'executed', 'cancelled'))
);

CREATE INDEX idx_multisig_txs_wallet ON multi_sig_transactions(multi_sig_id);
CREATE INDEX idx_multisig_txs_status ON multi_sig_transactions(status);
CREATE INDEX idx_multisig_txs_proposed ON multi_sig_transactions(proposed_at DESC);

-- ============================================================================
-- TABLE: multi_sig_approvals
-- Stores approvals for multi-sig transactions
-- ============================================================================

CREATE TABLE IF NOT EXISTS multi_sig_approvals (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL REFERENCES multi_sig_transactions(id) ON DELETE CASCADE,
    approver_id INTEGER REFERENCES users(id),
    approver_address VARCHAR(42) NOT NULL,
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    signature TEXT, -- Cryptographic signature
    
    CONSTRAINT unique_approval UNIQUE (transaction_id, approver_address)
);

CREATE INDEX idx_approvals_transaction ON multi_sig_approvals(transaction_id);
CREATE INDEX idx_approvals_approver ON multi_sig_approvals(approver_address);

-- ============================================================================
-- TABLE: sessions
-- Stores active user sessions
-- ============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(64) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_sessions_active ON sessions(is_active) WHERE is_active = TRUE;

-- ============================================================================
-- TABLE: audit_logs
-- Stores audit trail of all important actions
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL, -- login, logout, transaction, approval, etc.
    resource_type VARCHAR(50), -- wallet, transaction, contract, etc.
    resource_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action_type);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);

-- ============================================================================
-- TABLE: transaction_limits
-- Stores user-defined transaction limits
-- ============================================================================

CREATE TABLE IF NOT EXISTS transaction_limits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    max_gas_price DECIMAL(20, 9), -- In Gwei
    max_gas_limit BIGINT,
    max_total_cost DECIMAL(36, 18), -- In native currency
    max_priority_fee DECIMAL(20, 9), -- In Gwei
    daily_limit DECIMAL(36, 18),
    slippage_tolerance DECIMAL(5, 4) DEFAULT 0.01, -- 1%
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_limits_user ON transaction_limits(user_id);

-- ============================================================================
-- TABLE: gas_estimates
-- Stores historical gas estimates for analytics
-- ============================================================================

CREATE TABLE IF NOT EXISTS gas_estimates (
    id SERIAL PRIMARY KEY,
    chain_type VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- transfer, erc20, erc721_mint, etc.
    estimated_gas BIGINT NOT NULL,
    gas_price DECIMAL(20, 9) NOT NULL, -- In Gwei
    total_cost DECIMAL(36, 18) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gas_chain ON gas_estimates(chain_type);
CREATE INDEX idx_gas_type ON gas_estimates(transaction_type);
CREATE INDEX idx_gas_created ON gas_estimates(created_at DESC);

-- ============================================================================
-- TABLE: whitelist_addresses
-- Stores whitelisted addresses for additional security
-- ============================================================================

CREATE TABLE IF NOT EXISTS whitelist_addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address VARCHAR(42) NOT NULL,
    label VARCHAR(255),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT unique_user_address UNIQUE (user_id, address),
    CONSTRAINT eth_address_format CHECK (address ~* '^0x[a-fA-F0-9]{40}$')
);

CREATE INDEX idx_whitelist_user ON whitelist_addresses(user_id);
CREATE INDEX idx_whitelist_address ON whitelist_addresses(address);
CREATE INDEX idx_whitelist_active ON whitelist_addresses(user_id, is_active) WHERE is_active = TRUE;

-- ============================================================================
-- TABLE: token_balances
-- Cache token balances for quick access
-- ============================================================================

CREATE TABLE IF NOT EXISTS token_balances (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    token_address VARCHAR(42) NOT NULL,
    token_standard VARCHAR(20) NOT NULL, -- erc20, erc721, erc1155
    balance DECIMAL(36, 18) NOT NULL DEFAULT 0,
    token_id BIGINT, -- For NFTs
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_wallet_token UNIQUE (wallet_id, token_address, token_id)
);

CREATE INDEX idx_balances_wallet ON token_balances(wallet_id);
CREATE INDEX idx_balances_token ON token_balances(token_address);
CREATE INDEX idx_balances_updated ON token_balances(last_updated);

-- ============================================================================
-- TABLE: notifications
-- Stores user notifications
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL, -- transaction, approval, security, etc.
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Log all important actions to audit_logs
CREATE OR REPLACE FUNCTION log_transaction_audit()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        user_id, action_type, resource_type, resource_id, details
    ) VALUES (
        NEW.user_id, 
        'transaction_created', 
        'transaction', 
        NEW.id,
        jsonb_build_object(
            'tx_hash', NEW.tx_hash,
            'from_address', NEW.from_address,
            'to_address', NEW.to_address,
            'amount', NEW.amount,
            'chain_type', NEW.chain_type
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER transaction_audit_trigger
    AFTER INSERT ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION log_transaction_audit();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Recent transactions per user
CREATE OR REPLACE VIEW v_recent_transactions AS
SELECT 
    t.id,
    t.user_id,
    u.email,
    t.tx_hash,
    t.from_address,
    t.to_address,
    t.amount,
    t.chain_type,
    t.status,
    t.created_at
FROM transactions t
JOIN users u ON t.user_id = u.id
ORDER BY t.created_at DESC;

-- View: Multi-sig pending transactions with approval count
CREATE OR REPLACE VIEW v_multisig_pending AS
SELECT 
    mt.id,
    mt.multi_sig_id,
    mw.address AS multisig_address,
    mw.required_signatures,
    mt.tx_id,
    mt.to_address,
    mt.amount,
    mt.status,
    mt.proposed_at,
    COUNT(ma.id) AS approval_count,
    (COUNT(ma.id) >= mw.required_signatures) AS is_ready
FROM multi_sig_transactions mt
JOIN multi_sig_wallets mw ON mt.multi_sig_id = mw.id
LEFT JOIN multi_sig_approvals ma ON mt.id = ma.transaction_id
WHERE mt.status = 'pending'
GROUP BY mt.id, mw.id;

-- View: User wallet summary
CREATE OR REPLACE VIEW v_user_wallets AS
SELECT 
    u.id AS user_id,
    u.email,
    w.id AS wallet_id,
    w.address,
    w.chain_type,
    w.is_primary,
    w.label,
    COUNT(DISTINCT t.id) AS transaction_count,
    MAX(t.created_at) AS last_transaction
FROM users u
JOIN wallets w ON u.id = w.user_id
LEFT JOIN transactions t ON w.id = t.wallet_id
GROUP BY u.id, u.email, w.id;

-- ============================================================================
-- INITIAL DATA / CONFIGURATION
-- ============================================================================

-- Insert default transaction limits for new users (optional)
-- This can be triggered when a user is created

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to clean expired sessions
CREATE OR REPLACE FUNCTION clean_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get user statistics
CREATE OR REPLACE FUNCTION get_user_statistics(p_user_id INTEGER)
RETURNS TABLE (
    total_wallets BIGINT,
    total_transactions BIGINT,
    total_contracts BIGINT,
    total_multisig_wallets BIGINT,
    pending_multisig_txs BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM wallets WHERE user_id = p_user_id),
        (SELECT COUNT(*) FROM transactions WHERE user_id = p_user_id),
        (SELECT COUNT(*) FROM smart_contracts WHERE user_id = p_user_id),
        (SELECT COUNT(DISTINCT mo.multi_sig_id) 
         FROM multi_sig_owners mo 
         WHERE mo.user_id = p_user_id AND mo.is_active = TRUE),
        (SELECT COUNT(*) 
         FROM multi_sig_transactions mt
         JOIN multi_sig_owners mo ON mt.multi_sig_id = mo.multi_sig_id
         WHERE mo.user_id = p_user_id AND mt.status = 'pending');
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE users IS 'Stores user account information with authentication details';
COMMENT ON TABLE wallets IS 'Stores encrypted wallet keystores for each user';
COMMENT ON TABLE transactions IS 'Complete transaction history across all chains';
COMMENT ON TABLE smart_contracts IS 'Deployed smart contracts tracked by users';
COMMENT ON TABLE multi_sig_wallets IS 'Multi-signature wallet configurations';
COMMENT ON TABLE multi_sig_transactions IS 'Pending and executed multi-sig transactions';
COMMENT ON TABLE multi_sig_approvals IS 'Approval records for multi-sig transactions';
COMMENT ON TABLE sessions IS 'Active user sessions with expiration tracking';
COMMENT ON TABLE audit_logs IS 'Complete audit trail of all system actions';
COMMENT ON TABLE transaction_limits IS 'User-defined limits for transaction security';

-- ============================================================================
-- GRANT PERMISSIONS (Adjust based on your user roles)
-- ============================================================================

-- Example: Grant permissions to application user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================