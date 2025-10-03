# Nexus Enterprise Licensing System - Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [API Integration](#api-integration)
8. [CLI Integration](#cli-integration)
9. [License Management](#license-management)
10. [Security](#security)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The Nexus Enterprise Licensing System provides comprehensive license management for enterprise software applications with:

- **Multi-tier subscriptions**: Trial, Monthly, Annual, Enterprise, Perpetual
- **Feature flags**: Granular control over functionality
- **Machine activation**: Control deployment across devices
- **Usage tracking**: Monitor API calls and resource usage
- **Automatic renewal**: Subscription management
- **Enterprise security**: Encryption, authentication, audit logging

### Key Features

✅ License generation and validation  
✅ Machine-based activation (limit deployments)  
✅ Feature-based access control  
✅ Subscription management (monthly/annual)  
✅ API rate limiting  
✅ Comprehensive audit logging  
✅ Automatic expiration handling  
✅ CLI and REST API integration  
✅ PostgreSQL database backend  
✅ RSA-signed license keys  

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Nexus Application                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  REST API  │  │    CLI     │  │   Core     │           │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘           │
│        │                │                │                   │
│        └────────────────┴────────────────┘                   │
│                         │                                     │
└─────────────────────────┼─────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              License Manager (Decorator)                     │
│  • License Validation                                        │
│  • Feature Checking                                          │
│  • Rate Limiting                                             │
│  • Usage Tracking                                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  PostgreSQL Database                         │
│  ┌───────────┐  ┌──────────────┐  ┌────────────┐          │
│  │ Licenses  │  │  Activations │  │  Activity  │          │
│  └───────────┘  └──────────────┘  └────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Core Tables

#### 1. **customers**
Stores customer information
```sql
customer_id      UUID PRIMARY KEY
customer_name    VARCHAR(255)
customer_email   VARCHAR(255) UNIQUE
company_name     VARCHAR(255)
country          VARCHAR(100)
created_at       TIMESTAMP
```

#### 2. **licenses**
Main license records
```sql
license_id              SERIAL PRIMARY KEY
license_key             VARCHAR(50) UNIQUE
customer_id             UUID FK
license_type            VARCHAR(20) -- trial, monthly, annual, enterprise
status                  VARCHAR(20) -- active, expired, suspended
issue_date              TIMESTAMP
expiry_date             TIMESTAMP
features                JSONB
max_users               INTEGER
max_jobs                INTEGER
max_api_calls_per_day   INTEGER
```

#### 3. **machine_activations**
Track activated machines
```sql
activation_id    SERIAL PRIMARY KEY
license_key      VARCHAR(50) FK
machine_id       VARCHAR(64)
activated_at     TIMESTAMP
deactivated_at   TIMESTAMP
hostname         VARCHAR(255)
```

#### 4. **license_activity**
Audit log (partitioned)
```sql
activity_id         BIGSERIAL PRIMARY KEY
license_key         VARCHAR(50) FK
activity_type       VARCHAR(50)
activity_details    JSONB
activity_timestamp  TIMESTAMP
```

#### 5. **api_usage**
API call tracking (partitioned)
```sql
usage_id          BIGSERIAL PRIMARY KEY
license_key       VARCHAR(50) FK
call_timestamp    TIMESTAMP
endpoint          VARCHAR(255)
response_code     INTEGER
```

### Key Views

**v_active_licenses**: All active licenses with machine counts  
**v_license_usage_summary**: Usage statistics per license  
**v_expiring_licenses**: Licenses expiring in next 30 days  

---

## Installation

### 1. Prerequisites

```bash
# PostgreSQL 12+
sudo apt-get install postgresql-12

# Python 3.8+
python3 --version

# Required Python packages
pip install psycopg2-binary cryptography pyjwt
```

### 2. Database Setup

```bash
# Create database user
sudo -u postgres createuser nexus

# Create database
sudo -u postgres createdb nexus_licenses

# Apply schema
psql -U nexus -d nexus_licenses -f schema.sql
```

### 3. Environment Configuration

Create `.env` file:

```bash
# Database configuration
LICENSE_DB_HOST=localhost
LICENSE_DB_PORT=5432
LICENSE_DB_NAME=nexus_licenses
LICENSE_DB_USER=nexus
LICENSE_DB_PASSWORD=your_secure_password

# License system secret
NEXUS_SECRET_KEY=your_32_byte_secret_key

# Application license key (for deployed instances)
NEXUS_LICENSE_KEY=NEXUS-XXXX-XXXX-XXXX-XXXX
```

### 4. Generate RSA Keys

```bash
# Keys are automatically generated on first run
# Or manually generate:
openssl genrsa -out private_key.pem 2048
openssl rsa -in private_key.pem -pubout -out public_key.pem
```

---

## Configuration

### License Types

| Type | Duration | Features | Max Users | Use Case |
|------|----------|----------|-----------|----------|
| **TRIAL** | 14 days | Basic | 1 | Evaluation |
| **MONTHLY** | 30 days | Standard | 5 | Small teams |
| **ANNUAL** | 365 days | Advanced | 25 | Growing companies |
| **ENTERPRISE** | Custom | All | Unlimited | Large organizations |
| **PERPETUAL** | Lifetime | All | Unlimited | One-time purchase |

### Features

| Feature | Description | Required License |
|---------|-------------|------------------|
| `basic_etl` | Basic ETL operations | Trial+ |
| `advanced_etl` | Advanced ETL with transformations | Monthly+ |
| `database_management` | Full database tools | Trial+ |
| `pipeline_automation` | Automated pipelines | Monthly+ |
| `api_access` | REST API access | Trial+ |
| `cloud_connectors` | S3, Azure, GCS connectors | Monthly+ |
| `custom_code` | Python code execution | Annual+ |
| `enterprise_support` | 24/7 support | Enterprise |
| `unlimited_jobs` | No job limits | Enterprise |
| `priority_support` | Priority queue | Enterprise |

---

## Usage Examples

### Example 1: Generate License

```python
from nexus_licensing import LicenseManager, LicenseType, FeatureFlag

# Initialize manager
manager = LicenseManager(
    db_config={
        'host': 'localhost',
        'database': 'nexus_licenses',
        'user': 'nexus',
        'password': 'password'
    },
    secret_key='your-secret-key'
)

# Generate annual license
license = manager.generate_license(
    customer_name="Acme Corporation",
    customer_email="admin@acme.com",
    license_type=LicenseType.ANNUAL,
    max_users=10,
    max_jobs=100
)

print(f"License Key: {license.license_key}")
print(f"Expires: {license.expiry_date}")
print(f"Features: {[f.value for f in license.features]}")
```

**Output:**
```
License Key: NEXUS-A7K9-M3P2-X8Q4-Z6R1
Expires: 2025-10-02 14:30:00
Features: ['basic_etl', 'advanced_etl', 'database_management', 'pipeline_automation', 'api_access', 'cloud_connectors', 'custom_code']
```

### Example 2: Validate License

```python
from nexus_licensing import get_license_manager, get_machine_id

manager = get_license_manager()

# Validate license
result = manager.validate_license(
    license_key="NEXUS-A7K9-M3P2-X8Q4-Z6R1",
    machine_id=get_machine_id()
)

if result.is_valid:
    print(f"✓ License valid")
    print(f"  Days remaining: {result.remaining_days}")
    print(f"  Customer: {result.license.customer_name}")
else:
    print(f"✗ License invalid: {result.error_message}")
```

### Example 3: Machine Activation

```python
# Activate current machine
license_key = "NEXUS-A7K9-M3P2-X8Q4-Z6R1"
machine_id = get_machine_id()

success = manager.activate_machine(license_key, machine_id)

if success:
    print(f"✓ Machine activated: {machine_id[:8]}...")
else:
    print("✗ Activation failed")

# Check activation status
is_activated = manager._is_machine_activated(license_key, machine_id)
print(f"Activated: {is_activated}")

# Deactivate
manager.deactivate_machine(license_key, machine_id)
```

### Example 4: Feature Checking

```python
from nexus_licensing import FeatureFlag

license_key = "NEXUS-A7K9-M3P2-X8Q4-Z6R1"

# Check specific feature
has_cloud = manager.has_feature(license_key, FeatureFlag.CLOUD_CONNECTORS)
print(f"Cloud connectors: {has_cloud}")

has_enterprise = manager.has_feature(license_key, FeatureFlag.ENTERPRISE_SUPPORT)
print(f"Enterprise support: {has_enterprise}")

# Add feature
manager.add_feature(license_key, FeatureFlag.ENTERPRISE_SUPPORT)
```

### Example 5: License Renewal

```python
# Renew for 30 more days
success = manager.renew_license(
    license_key="NEXUS-A7K9-M3P2-X8Q4-Z6R1",
    extend_days=30
)

if success:
    # Get updated info
    info = manager.get_license_info(license_key)
    print(f"✓ License renewed")
    print(f"  New expiry: {info['expiry_date']}")
    print(f"  Days remaining: {info['remaining_days']}")
```

### Example 6: Usage Tracking

```python
# Track API call
manager.track_api_call(license_key)

# Check usage
usage_today = manager.get_api_usage_today(license_key)
print(f"API calls today: {usage_today}")

# Check rate limit
within_limit = manager.check_rate_limit(license_key)
if not within_limit:
    print("⚠️  Rate limit exceeded")
```

### Example 7: Complete License Info

```python
info = manager.get_license_info("NEXUS-A7K9-M3P2-X8Q4-Z6R1")

print(json.dumps(info, indent=2))
```

**Output:**
```json
{
  "license_key": "NEXUS-A7K9-M3P2-X8Q4-Z6R1",
  "customer_name": "Acme Corporation",
  "customer_email": "admin@acme.com",
  "type": "annual",
  "status": "active",
  "is_valid": true,
  "issue_date": "2024-10-02T14:30:00",
  "expiry_date": "2025-10-02T14:30:00",
  "remaining_days": 365,
  "features": [
    "basic_etl",
    "advanced_etl",
    "database_management",
    "pipeline_automation",
    "api_access",
    "cloud_connectors",
    "custom_code"
  ],
  "max_users": 10,
  "max_jobs": 100,
  "active_machines": 3,
  "api_usage_today": 247,
  "max_api_calls_per_day": 1000
}
```

---

## API Integration

### Using the License Decorator

The `@require_license` decorator automatically validates licenses for API endpoints:

```python
from flask import Flask, jsonify
from nexus_licensing import require_license, FeatureFlag

app = Flask(__name__)

# Basic endpoint - requires valid license
@app.route('/api/data')
@require_license()
def get_data():
    return jsonify({"data": "your data here"})

# Feature-restricted endpoint
@app.route('/api/etl/advanced')
@require_license(feature=FeatureFlag.ADVANCED_ETL)
def advanced_etl():
    return jsonify({"message": "Advanced ETL operation"})

# Cloud operations - requires cloud connector feature
@app.route('/api/s3/upload')
@require_license(feature=FeatureFlag.CLOUD_CONNECTORS)
def s3_upload():
    return jsonify({"message": "S3 upload initiated"})
```

### Error Responses

When license validation fails:

```python
# No license key configured
{
  "error": "No license key configured. Set NEXUS_LICENSE_KEY environment variable.",
  "status": 401
}

# Invalid license
{
  "error": "License validation failed: License has expired",
  "status": 403
}

# Missing feature
{
  "error": "License does not include feature: cloud_connectors",
  "status": 403
}

# Rate limit exceeded
{
  "error": "API rate limit exceeded",
  "status": 429
}
```

### REST API Endpoints for License Management

```python
from flask import Flask, request, jsonify
from nexus_licensing import get_license_manager, LicenseType

app = Flask(__name__)
manager = get_license_manager()

# Generate new license
@app.route('/admin/licenses', methods=['POST'])
def create_license():
    data = request.json
    
    license = manager.generate_license(
        customer_name=data['customer_name'],
        customer_email=data['customer_email'],
        license_type=LicenseType(data['license_type']),
        max_users=data.get('max_users', 1)
    )
    
    return jsonify({
        'license_key': license.license_key,
        'expiry_date': license.expiry_date.isoformat()
    }), 201

# Validate license
@app.route('/licenses/<license_key>/validate', methods=['GET'])
def validate_license(license_key):
    machine_id = request.args.get('machine_id')
    result = manager.validate_license(license_key, machine_id)
    
    return jsonify({
        'is_valid': result.is_valid,
        'error_message': result.error_message,
        'remaining_days': result.remaining_days
    })

# Get license info
@app.route('/licenses/<license_key>', methods=['GET'])
def get_license(license_key):
    info = manager.get_license_info(license_key)
    
    if not info:
        return jsonify({'error': 'License not found'}), 404
    
    return jsonify(info)

# Activate machine
@app.route('/licenses/<license_key>/activate', methods=['POST'])
def activate_machine(license_key):
    data = request.json
    machine_id = data['machine_id']
    
    success = manager.activate_machine(license_key, machine_id)
    
    if success:
        return jsonify({'message': 'Machine activated'}), 200
    else:
        return jsonify({'error': 'Activation failed'}), 400

# Renew license
@app.route('/licenses/<license_key>/renew', methods=['POST'])
def renew_license(license_key):
    data = request.json
    extend_days = data.get('extend_days')
    
    success = manager.renew_license(license_key, extend_days)
    
    if success:
        return jsonify({'message': 'License renewed'}), 200
    else:
        return jsonify({'error': 'Renewal failed'}), 400
```

---

## CLI Integration

### Example CLI Commands

```python
import click
from nexus_licensing import get_license_manager, get_machine_id, require_license

# Initialize manager
manager = get_license_manager()

@click.group()
def cli():
    """Nexus Enterprise CLI"""
    pass

@cli.command()
@click.option('--license-key', required=True, help='License key')
def activate(license_key):
    """Activate license on this machine"""
    machine_id = get_machine_id()
    
    success = manager.activate_machine(license_key, machine_id)
    
    if success:
        click.echo(f"✓ License activated on machine {machine_id[:8]}...")
    else:
        click.echo("✗ Activation failed", err=True)
        exit(1)

@cli.command()
def info():
    """Show license information"""
    license_key = os.getenv('NEXUS_LICENSE_KEY')
    
    if not license_key:
        click.echo("No license configured", err=True)
        exit(1)
    
    info = manager.get_license_info(license_key)
    
    if not info:
        click.echo("License not found", err=True)
        exit(1)
    
    click.echo(f"License Key: {info['license_key']}")
    click.echo(f"Customer: {info['customer_name']}")
    click.echo(f"Type: {info['type']}")
    click.echo(f"Status: {info['status']}")
    click.echo(f"Valid: {'Yes' if info['is_valid'] else 'No'}")
    click.echo(f"Expires: {info['expiry_date']}")
    click.echo(f"Days Remaining: {info['remaining_days']}")
    click.echo(f"Features: {', '.join(info['features'])}")
    click.echo(f"API Usage Today: {info['api_usage_today']}/{info['max_api_calls_per_day']}")

@cli.command()
@click.argument('job_name')
@require_license(feature=FeatureFlag.PIPELINE_AUTOMATION)
def run_job(job_name):
    """Run ETL job (requires license)"""
    click.echo(f"Running job: {job_name}")
    # Job execution logic here
    click.echo("✓ Job completed")

if __name__ == '__main__':
    cli()
```

### Usage

```bash
# Set license key
export NEXUS_LICENSE_KEY=NEXUS-A7K9-M3P2-X8Q4-Z6R1

# Activate license
python nexus.py activate --license-key NEXUS-A7K9-M3P2-X8Q4-Z6R1

# Show license info
python nexus.py info

# Run job (license validated automatically)
python nexus.py run-job daily-etl
```

---

## License Management

### Administrative Tasks

#### 1. Generate Trial License

```python
trial_license = manager.generate_license(
    customer_name="Trial User",
    customer_email="trial@example.com",
    license_type=LicenseType.TRIAL
)
# Valid for 14 days, basic features only
```

#### 2. Upgrade License

```python
# Get current license
license = manager._get_license(license_key)

# Add enterprise features
manager.add_feature(license_key, FeatureFlag.ENTERPRISE_SUPPORT)
manager.add_feature(license_key, FeatureFlag.UNLIMITED_JOBS)

# Update limits
with manager._get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE licenses
            SET max_users = 100,
                max_jobs = -1,  -- unlimited
                license_type = 'enterprise'
            WHERE license_key = %s
        """, (license_key,))
        conn.commit()
```

#### 3. Suspend License

```python
manager._update_license_status(license_key, LicenseStatus.SUSPENDED)
```

#### 4. Revoke License

```python
manager._update_license_status(license_key, LicenseStatus.REVOKED)

# Deactivate all machines
with manager._get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE machine_activations
            SET deactivated_at = NOW()
            WHERE license_key = %s
        """, (license_key,))
        conn.commit()
```

#### 5. Bulk Operations

```python
# Find expiring licenses
with manager._get_db_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT * FROM v_expiring_licenses
            WHERE days_until_expiry <= 7
        """)
        expiring = cur.fetchall()

# Send renewal reminders
for license in expiring:
    send_renewal_email(
        license['customer_email'],
        license['license_key'],
        license['days_until_expiry']
    )
```

#### 6. Analytics Queries

```python
# License statistics
with manager._get_db_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM get_license_stats()")
        stats = cur.fetchone()

print(f"Total Licenses: {stats['total_licenses']}")
print(f"Active: {stats['active_licenses']}")
print(f"Revenue: ${stats['total_revenue']}")

# Top customers by usage
cur.execute("""
    SELECT 
        l.customer_name,
        COUNT(au.usage_id) as api_calls,
        COUNT(DISTINCT ma.machine_id) as machines
    FROM licenses l
    LEFT JOIN api_usage au ON l.license_key = au.license_key
    LEFT JOIN machine_activations ma ON l.license_key = ma.license_key
    WHERE au.call_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY l.customer_name
    ORDER BY api_calls DESC
    LIMIT 10
""")
top_customers = cur.fetchall()
```

---

## Security

### 1. Encryption

All sensitive data is encrypted:

```python
# Connection parameters are encrypted when stored
source = DataSource(
    name="secure_db",
    connection_params={
        'password': 'my-password'  # Will be encrypted
    },
    encrypted=True
)
```

### 2. RSA Signing

License keys are cryptographically signed:

```python
# Signature verification
def verify_license_signature(license_key: str, signature: bytes) -> bool:
    public_key = load_public_key()
    
    try:
        public_key.verify(
            signature,
            license_key.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except:
        return False
```

### 3. Audit Logging

All operations are logged:

```sql
SELECT 
    activity_type,
    COUNT(*) as count,
    MAX(activity_timestamp) as last_occurrence
FROM license_activity
WHERE license_key = 'NEXUS-XXXX-XXXX-XXXX-XXXX'
GROUP BY activity_type
ORDER BY last_occurrence DESC;
```

### 4. Rate Limiting

Prevent abuse with rate limiting:

```python
@app.before_request
def check_rate_limit():
    license_key = request.headers.get('X-License-Key')
    
    if license_key:
        manager = get_license_manager()
        
        if not manager.check_rate_limit(license_key):
            return jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': 3600  # seconds
            }), 429
```

### 5. Secure Storage

Store license keys securely:

```bash
# Use environment variables
export NEXUS_LICENSE_KEY=NEXUS-XXXX-XXXX-XXXX-XXXX

# Or encrypted config file
openssl enc -aes-256-cbc -salt \
    -in license.txt \
    -out license.enc \
    -pass pass:your-password

# Decrypt when needed
openssl enc -aes-256-cbc -d \
    -in license.enc \
    -out license.txt \
    -pass pass:your-password
```

---

## Troubleshooting

### Issue 1: License Validation Fails

**Problem:** License validation returns "Invalid license key"

**Solutions:**
```python
# 1. Check if license exists in database
SELECT * FROM licenses WHERE license_key = 'NEXUS-...';

# 2. Verify license status
SELECT status, expiry_date FROM licenses WHERE license_key = 'NEXUS-...';

# 3. Check for expired licenses
UPDATE licenses SET status = 'expired' 
WHERE status = 'active' AND expiry_date < NOW();

# 4. Verify machine activation
SELECT * FROM machine_activations 
WHERE license_key = 'NEXUS-...' AND deactivated_at IS NULL;
```

### Issue 2: Rate Limit Exceeded

**Problem:** API calls fail with 429 status

**Solutions:**
```python
# 1. Check current usage
usage = manager.get_api_usage_today(license_key)
print(f"Usage: {usage}/{max_calls}")

# 2. Reset daily counter (admin only)
DELETE FROM api_usage 
WHERE license_key = 'NEXUS-...' 
AND call_timestamp >= CURRENT_DATE;

# 3. Increase limit
UPDATE licenses 
SET max_api_calls_per_day = 10000 
WHERE license_key = 'NEXUS-...';
```

### Issue 3: Machine Activation Limit Reached

**Problem:** Cannot activate on new machine

**Solutions:**
```python
# 1. List active machines
SELECT machine_id, hostname, activated_at, last_seen_at
FROM machine_activations
WHERE license_key = 'NEXUS-...' AND deactivated_at IS NULL;

# 2. Deactivate old machines
manager.deactivate_machine(license_key, old_machine_id)

# 3. Increase limit
UPDATE licenses SET max_users = 20 WHERE license_key = 'NEXUS-...';
```

### Issue 4: License Expired

**Problem:** Operations fail with "License has expired"

**Solutions:**
```python
# 1. Renew license
manager.renew_license(license_key, extend_days=365)

# 2. Check expiry date
info = manager.get_license_info(license_key)
print(f"Expires: {info['expiry_date']}")
print(f"Days remaining: {info['remaining_days']}")

# 3. Manual extension
UPDATE licenses 
SET expiry_date = expiry_date + INTERVAL '365 days',
    status = 'active'
WHERE license_key = 'NEXUS-...';
```

### Issue 5: Database Connection Errors

**Problem:** Cannot connect to license database

**Solutions:**
```bash
# 1. Test connection
psql -h localhost -U nexus -d nexus_licenses -c "SELECT 1;"

# 2. Check PostgreSQL service
sudo systemctl status postgresql

# 3. Verify credentials
echo $LICENSE_DB_PASSWORD

# 4. Check firewall
sudo ufw allow 5432/tcp

# 5. Review pg_hba.conf
sudo nano /etc/postgresql/12/main/pg_hba.conf
```

---

## Best Practices

### 1. License Key Distribution

- Never commit license keys to version control
- Use environment variables or secure vaults
- Rotate keys periodically for security
- Maintain separate keys for dev/staging/production

### 2. Monitoring

```python
# Setup monitoring for:
# - Expiring licenses (30 days notice)
# - High API usage (>80% of limit)
# - Failed validation attempts
# - Suspicious activation patterns

# Example: Daily expiration check
def check_expiring_licenses():
    with manager._get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM v_expiring_licenses")
            expiring = cur.fetchall()
            
            for license in expiring:
                if license['days_until_expiry'] <= 7:
                    alert_team(f"License {license['license_key']} expires in {license['days_until_expiry']} days")
```

### 3. Backup Strategy

```bash
# Daily backup
pg_dump -h localhost -U nexus nexus_licenses | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore from backup
gunzip -c backup_20241002.sql.gz | psql -h localhost -U nexus nexus_licenses
```

### 4. Performance Optimization

```sql
-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_licenses_expiry_status 
ON licenses(expiry_date, status) 
WHERE status = 'active';

-- Partition old data
CREATE TABLE api_usage_archive AS 
SELECT * FROM api_usage 
WHERE call_timestamp < CURRENT_DATE - INTERVAL '90 days';

DELETE FROM api_usage 
WHERE call_timestamp < CURRENT_DATE - INTERVAL '90 days';

-- Analyze tables
ANALYZE licenses;
ANALYZE api_usage;
```

---

## Support

- Documentation: https://docs.nexus-framework.com/licensing
- Email: licensing@nexus-framework.com
- Support Portal: https://support.nexus-framework.com
- Emergency: +1-800-NEXUS-911

---

## License Agreement

This licensing system is proprietary software. Unauthorized use, reproduction, or distribution is prohibited.

© 2024 Nexus Enterprise. All rights reserved.