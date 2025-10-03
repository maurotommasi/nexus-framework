# Nexus Enterprise ETL System - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Security Features](#security-features)
4. [Data Sources & Targets](#data-sources--targets)
5. [Transformations](#transformations)
6. [100 Use Cases](#100-use-cases)
7. [API Reference](#api-reference)
8. [Best Practices](#best-practices)

---

## Overview

The Nexus Enterprise ETL System is a production-ready, highly scalable Extract-Transform-Load framework designed for enterprise data integration needs.

### Key Features
- **Multi-Source Support**: Databases, APIs, Files, Cloud Storage (S3, Azure, GCS)
- **Advanced Transformations**: Built-in operations + custom Python code
- **Enterprise Security**: End-to-end encryption, credential management, audit logging
- **High Performance**: Parallel processing, batch operations, connection pooling
- **Monitoring**: Real-time metrics, execution history, error tracking
- **Scheduling**: Cron-based job scheduling with retry logic

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ETL Manager                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Job Registry │  │  Scheduler   │  │   Monitor    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       ETL Executor                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Extract    │─▶│  Transform   │─▶│     Load     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐      ┌────────────────┐   ┌─────────────┐
│   Sources   │      │Transformation  │   │  Targets    │
│             │      │    Engine      │   │             │
│ • Database  │      │                │   │ • Database  │
│ • API       │      │ • Filter       │   │ • File      │
│ • File      │      │ • Map          │   │ • Cloud     │
│ • Cloud     │      │ • Aggregate    │   │ • API       │
│ • FTP/SFTP  │      │ • Custom Code  │   │             │
└─────────────┘      └────────────────┘   └─────────────┘
```

---

## Security Features

### 1. End-to-End Encryption

```python
from etl_core import SecurityManager

# Initialize security manager
security = SecurityManager(master_key="your-secure-key")

# Encrypt sensitive data
encrypted = security.encrypt("my-password")

# Connection parameters are automatically encrypted
source = DataSource(
    name="secure_db",
    source_type=SourceType.DATABASE,
    connection_params={
        'type': 'postgresql',
        'password': 'sensitive-password'  # Will be encrypted
    },
    encrypted=True  # Enable encryption
)
```

### 2. Credential Management

Store credentials securely:

```python
# .env file
DATABASE_PASSWORD=my-secret-pass
API_KEY=abc123xyz

# In code
import os
from dotenv import load_dotenv

load_dotenv()

connection_params = {
    'password': os.getenv('DATABASE_PASSWORD'),
    'api_key': os.getenv('API_KEY')
}
```

### 3. Audit Logging

All ETL operations are automatically logged:

```python
# View audit logs
metrics = manager.get_job_metrics(job_id)
for m in metrics:
    print(f"Run: {m.run_id}")
    print(f"Status: {m.status}")
    print(f"Rows: {m.rows_extracted} → {m.rows_loaded}")
    print(f"Errors: {m.errors}")
```

### 4. Network Security

```python
# Use TLS/SSL for API connections
source = DataSource(
    name="secure_api",
    source_type=SourceType.API,
    connection_params={},
    api_endpoint="https://api.example.com/data",  # HTTPS only
    api_headers={
        'Authorization': 'Bearer ' + os.getenv('API_TOKEN'),
        'X-API-Key': os.getenv('API_KEY')
    }
)
```

---

## Data Sources & Targets

### Supported Sources

| Source Type | Description | Parameters |
|------------|-------------|------------|
| DATABASE | PostgreSQL, MySQL, SQLite, Oracle, SQL Server, MongoDB | host, port, database, user, password |
| API | REST APIs with authentication | endpoint, method, headers, params |
| FILE | CSV, Excel, JSON, Parquet | file_path, file_format |
| S3 | AWS S3 buckets | bucket, access_key, secret_key, region |
| AZURE_BLOB | Azure Blob Storage | account_name, account_key, container |
| GCS | Google Cloud Storage | project_id, credentials, bucket |
| FTP/SFTP | File transfer protocols | host, username, password, port |
| KAFKA | Apache Kafka streams | brokers, topic, consumer_group |
| REDIS | Redis cache/database | host, port, db, password |
| ELASTICSEARCH | Elasticsearch indices | host, index, query |

### Database Source Example

```python
source = DataSource(
    name="postgres_source",
    source_type=SourceType.DATABASE,
    connection_params={
        'type': 'postgresql',
        'host': 'localhost',
        'port': 5432,
        'database': 'mydb',
        'user': 'postgres',
        'password': 'password'
    },
    table='users',
    # OR use custom query
    query="""
        SELECT u.*, o.total_orders
        FROM users u
        LEFT JOIN (
            SELECT user_id, COUNT(*) as total_orders
            FROM orders
            GROUP BY user_id
        ) o ON u.id = o.user_id
        WHERE u.created_at >= '2024-01-01'
    """,
    # Incremental loading
    incremental_column='updated_at',
    incremental_value='2024-01-01 00:00:00',
    batch_size=10000
)
```

### API Source Example

```python
source = DataSource(
    name="rest_api",
    source_type=SourceType.API,
    connection_params={},
    api_endpoint="https://api.example.com/v1/customers",
    api_method="GET",
    api_headers={
        'Authorization': 'Bearer TOKEN',
        'Content-Type': 'application/json'
    },
    api_params={
        'page_size': 100,
        'status': 'active'
    }
)
```

### File Source Example

```python
source = DataSource(
    name="csv_file",
    source_type=SourceType.FILE,
    connection_params={},
    file_path='/data/input/customers.csv',
    file_format='csv'
)
```

### S3 Source Example

```python
source = DataSource(
    name="s3_data",
    source_type=SourceType.S3,
    connection_params={
        'bucket': 'my-data-bucket',
        'access_key': 'AKIAIOSFODNN7EXAMPLE',
        'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        'region': 'us-east-1'
    },
    file_path='data/2024/customers.parquet',
    file_format='parquet'
)
```

---

## Transformations

### Built-in Transformations

#### 1. Filter
```python
Transformation(
    name="filter_active",
    transformation_type=TransformationType.FILTER,
    config={
        'condition': 'status == "active" and age >= 18'
    },
    order=1
)
```

#### 2. Map (Column Mapping)
```python
Transformation(
    name="create_columns",
    transformation_type=TransformationType.MAP,
    config={
        'mappings': {
            'full_name': 'first_name + " " + last_name',
            'revenue': 'quantity * price',
            'discount_amount': 'revenue * discount_rate'
        }
    },
    order=2
)
```

#### 3. Aggregate
```python
Transformation(
    name="summarize",
    transformation_type=TransformationType.AGGREGATE,
    config={
        'group_by': ['customer_id', 'product_category'],
        'aggregations': {
            'total_sales': ('amount', 'sum'),
            'order_count': ('order_id', 'count'),
            'avg_order_value': ('amount', 'mean')
        }
    },
    order=3
)
```

#### 4. Sort
```python
Transformation(
    name="sort_data",
    transformation_type=TransformationType.SORT,
    config={
        'columns': ['date', 'amount'],
        'ascending': [False, False]
    },
    order=4
)
```

#### 5. Deduplicate
```python
Transformation(
    name="remove_duplicates",
    transformation_type=TransformationType.DEDUPLICATE,
    config={
        'subset': ['email', 'date'],
        'keep': 'last'  # or 'first'
    },
    order=5
)
```

#### 6. Pivot
```python
Transformation(
    name="pivot_sales",
    transformation_type=TransformationType.PIVOT,
    config={
        'index': 'customer_id',
        'columns': 'month',
        'values': 'sales'
    },
    order=6
)
```

### Custom Python Code Transformations

The most powerful feature - execute any Python code:

```python
Transformation(
    name="advanced_processing",
    transformation_type=TransformationType.CUSTOM_CODE,
    custom_code="""
# Available variables: df, pd, np, datetime, timedelta

# 1. Data cleaning
df['email'] = df['email'].str.lower().str.strip()
df['phone'] = df['phone'].str.replace(r'\\D', '', regex=True)

# 2. Feature engineering
df['customer_lifetime_days'] = (pd.Timestamp.now() - pd.to_datetime(df['first_purchase_date'])).dt.days
df['is_vip'] = df['total_spent'] > 10000

# 3. Complex calculations
df['loyalty_score'] = (
    df['order_count'] * 10 +
    df['total_spent'] / 100 +
    df['customer_lifetime_days'] / 365 * 50
).clip(0, 1000)

# 4. Conditional logic
def categorize_customer(row):
    if row['total_spent'] > 50000:
        return 'Enterprise'
    elif row['total_spent'] > 10000:
        return 'Premium'
    elif row['total_spent'] > 1000:
        return 'Standard'
    else:
        return 'Basic'

df['customer_tier'] = df.apply(categorize_customer, axis=1)

# 5. Date/time operations
df['month'] = pd.to_datetime(df['order_date']).dt.month
df['quarter'] = pd.to_datetime(df['order_date']).dt.quarter
df['days_since_last_order'] = (pd.Timestamp.now() - pd.to_datetime(df['last_order_date'])).dt.days

# 6. Statistical operations
df['sales_zscore'] = (df['sales'] - df['sales'].mean()) / df['sales'].std()
df['sales_percentile'] = df['sales'].rank(pct=True)

# 7. Text processing
df['email_domain'] = df['email'].str.split('@').str[1]
df['name_length'] = df['full_name'].str.len()

# 8. External API calls (with caution)
import requests
# df['enriched_data'] = df['customer_id'].apply(lambda x: call_api(x))

# 9. Data validation
df = df[df['age'].between(0, 120)]
df = df[df['email'].str.contains('@', na=False)]

# 10. Output
print(f"Processed {len(df)} rows")
""",
    order=1
)
```

---

## 100 Use Cases

### Category 1: Database to Database (Cases 1-15)

#### 1. PostgreSQL to MySQL Migration
```python
job = ETLJob(
    job_id=str(uuid.uuid4()),
    name="PG to MySQL",
    description="Migrate users table",
    sources=[DataSource(
        name="pg_source",
        source_type=SourceType.DATABASE,
        connection_params={'type': 'postgresql', 'host': 'pg.host', 'database': 'db1'},
        table='users'
    )],
    transformations=[],
    targets=[DataTarget(
        name="mysql_target",
        target_type=TargetType.DATABASE,
        connection_params={'type': 'mysql', 'host': 'mysql.host', 'database': 'db2'},
        table='users',
        write_mode='overwrite'
    )]
)
```

#### 2. Incremental Data Sync
```python
source = DataSource(
    name="incremental_source",
    source_type=SourceType.DATABASE,
    connection_params={'type': 'postgresql', ...},
    table='orders',
    incremental_column='updated_at',
    incremental_value='2024-01-01 00:00:00'
)
```

#### 3. Multi-Table Join and Load
```python
source = DataSource(
    name="joined_data",
    source_type=SourceType.DATABASE,
    query="""
        SELECT 
            o.order_id,
            o.order_date,
            c.customer_name,
            p.product_name,
            o.quantity * p.price as total
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        JOIN products p ON o.product_id = p.id
        WHERE o.order_date >= '2024-01-01'
    """
)
```

#### 4. Data Aggregation Pipeline
```python
transformations = [
    Transformation(
        name="aggregate_sales",
        transformation_type=TransformationType.AGGREGATE,
        config={
            'group_by': ['customer_id', 'product_category'],
            'aggregations': {
                'total_revenue': ('amount', 'sum'),
                'total_orders': ('order_id', 'count'),
                'avg_order_value': ('amount', 'mean'),
                'max_order': ('amount', 'max')
            }
        }
    )
]
```

#### 5. Data Denormalization
```python
# From normalized to denormalized structure
custom_code = """
# Pivot category sales
pivot_df = df.pivot_table(
    index='customer_id',
    columns='category',
    values='sales',
    aggfunc='sum',
    fill_value=0
)

# Flatten column names
pivot_df.columns = [f'sales_{col}' for col in pivot_df.columns]

# Merge back
df = df.merge(pivot_df, on='customer_id', how='left')
"""
```

#### 6. Slowly Changing Dimension (SCD) Type 2
```python
custom_code = """
# SCD Type 2 implementation
df['valid_from'] = pd.Timestamp.now()
df['valid_to'] = pd.Timestamp('2099-12-31')
df['is_current'] = True
df['version'] = 1

# Check for changes and create new versions
# (simplified - full implementation requires comparing with existing data)
"""
```

#### 7-15. Additional Database Patterns
- **7**: Cross-database data consolidation
- **8**: Database archiving (move old data to archive DB)
- **9**: Data quality validation before load
- **10**: Real-time CDC (Change Data Capture) simulation
- **11**: Multi-tenant database synchronization
- **12**: Database replication with transformation
- **13**: Historical data reconstruction
- **14**: Database performance optimization via materialized views
- **15**: Master data management sync

---

### Category 2: API to Database (Cases 16-30)

#### 16. REST API to PostgreSQL
```python
source = DataSource(
    name="rest_api",
    source_type=SourceType.API,
    api_endpoint="https://api.stripe.com/v1/charges",
    api_method="GET",
    api_headers={'Authorization': 'Bearer sk_test_...'},
    api_params={'limit': 100}
)

target = DataTarget(
    name="pg_db",
    target_type=TargetType.DATABASE,
    connection_params={'type': 'postgresql', ...},
    table='stripe_charges',
    write_mode='append'
)
```

#### 17. Paginated API Extract
```python
custom_code = """
# Handle paginated results
all_data = []
page = 1
while True:
    response = requests.get(
        'https://api.example.com/data',
        params={'page': page, 'size': 100}
    )
    data = response.json()
    
    if not data['results']:
        break
    
    all_data.extend(data['results'])
    page += 1

df = pd.DataFrame(all_data)
"""
```

#### 18. API Rate Limiting Handler
```python
import time

custom_code = """
# Respect rate limits
def fetch_with_rate_limit(ids, calls_per_second=10):
    results = []
    for i, id in enumerate(ids):
        response = requests.get(f'https://api.example.com/item/{id}')
        results.append(response.json())
        
        if (i + 1) % calls_per_second == 0:
            time.sleep(1)
    
    return results

# Apply to dataframe
df['api_data'] = fetch_with_rate_limit(df['id'].tolist())
"""
```

#### 19. JSON Flattening
```python
custom_code = """
# Flatten nested JSON from API
from pandas import json_normalize

df_flat = json_normalize(df['nested_json'])
df = pd.concat([df.drop('nested_json', axis=1), df_flat], axis=1)
"""
```

#### 20. OAuth2 API Integration
```python
source = DataSource(
    name="oauth_api",
    source_type=SourceType.API,
    connection_params={},
    api_endpoint="https://api.example.com/data",
    api_headers={
        'Authorization': f'Bearer {get_oauth_token()}',
        'Content-Type': 'application/json'
    }
)
```

#### 21-30. Additional API Patterns
- **21**: GraphQL API to database
- **22**: SOAP API integration
- **23**: Webhook data capture
- **24**: Social media API (Twitter, Facebook)
- **25**: Payment gateway integration (Stripe, PayPal)
- **26**: CRM API sync (Salesforce, HubSpot)
- **27**: Marketing automation API (Mailchimp, SendGrid)
- **28**: Analytics API (Google Analytics, Mixpanel)
- **29**: Weather data API integration
- **30**: Stock market API to database

---

### Category 3: File Processing (Cases 31-45)

#### 31. CSV to Database
```python
source = DataSource(
    name="csv_file",
    source_type=SourceType.FILE,
    file_path='/data/customers.csv',
    file_format='csv'
)
```

#### 32. Excel Multi-Sheet Processing
```python
custom_code = """
# Read multiple sheets
excel_file = pd.ExcelFile('/data/report.xlsx')

dfs = []
for sheet_name in excel_file.sheet_names:
    df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name)
    df_sheet['source_sheet'] = sheet_name
    dfs.append(df_sheet)

df = pd.concat(dfs, ignore_index=True)
"""
```

#### 33. JSON Lines Processing
```python
custom_code = """
# Process JSON Lines (JSONL) format
import json

records = []
with open('/data/logs.jsonl', 'r') as f:
    for line in f:
        records.append(json.loads(line))

df = pd.DataFrame(records)
"""
```

#### 34. Parquet Optimization
```python
target = DataTarget(
    name="parquet_output",
    target_type=TargetType.FILE,
    file_path='/data/output/customers.parquet',
    file_format='parquet'
)
```

#### 35. Data Validation with Great Expectations
```python
custom_code = """
# Data quality validation
def validate_data(df):
    errors = []
    
    # Check for nulls
    if df['email'].isnull().any():
        errors.append('Email has null values')
    
    # Check data types
    if df['age'].dtype != 'int64':
        errors.append('Age is not integer')
    
    # Check ranges
    if (df['age'] < 0).any() or (df['age'] > 120).any():
        errors.append('Age out of valid range')
    
    # Check uniqueness
    if df['email'].duplicated().any():
        errors.append('Duplicate emails found')
    
    if errors:
        raise ValueError(f"Validation failed: {errors}")
    
    return df

df = validate_data(df)
"""
```

#### 36-45. Additional File Patterns
- **36**: PDF text extraction to database
- **37**: Image metadata extraction
- **38**: Log file parsing and analysis
- **39**: ZIP file batch processing
- **40**: XML to JSON conversion
- **41**: Fixed-width file parsing
- **42**: Multi-file concatenation
- **43**: File format conversion pipeline
- **44**: Large file chunked processing
- **45**: Encrypted file decryption and load

---

### Category 4: Cloud Storage (Cases 46-60)

#### 46. S3 to Database
```python
source = DataSource(
    name="s3_source",
    source_type=SourceType.S3,
    connection_params={
        'bucket': 'my-data-bucket',
        'access_key': os.getenv('AWS_ACCESS_KEY'),
        'secret_key': os.getenv('AWS_SECRET_KEY'),
        'region': 'us-east-1'
    },
    file_path='data/customers.parquet'
)
```

#### 47. S3 Batch Processing
```python
custom_code = """
import boto3

s3 = boto3.client('s3')
bucket = 'my-bucket'
prefix = 'data/2024/'

# List all files
response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

dfs = []
for obj in response.get('Contents', []):
    key = obj['Key']
    if key.endswith('.csv'):
        # Download and read
        local_path = f'/tmp/{key.split("/")[-1]}'
        s3.download_file(bucket, key, local_path)
        dfs.append(pd.read_csv(local_path))

df = pd.concat(dfs, ignore_index=True)
"""
```

#### 48. Azure Blob Storage
```python
source = DataSource(
    name="azure_blob",
    source_type=SourceType.AZURE_BLOB,
    connection_params={
        'account_name': 'mystorageaccount',
        'account_key': os.getenv('AZURE_STORAGE_KEY'),
        'container': 'data-container'
    },
    file_path='customers/2024/data.csv'
)
```

#### 49. Google Cloud Storage
```python
source = DataSource(
    name="gcs_source",
    source_type=SourceType.GCS,
    connection_params={
        'project_id': 'my-project',
        'credentials': '/path/to/service-account.json',
        'bucket': 'my-gcs-bucket'
    },
    file_path='data/customers.parquet'
)
```

#### 50. Cross-Cloud Migration (S3 to Azure)
```python
# Source: S3
source = DataSource(name="s3", source_type=SourceType.S3, ...)

# Target: Azure
target = DataTarget(name="azure", target_type=TargetType.AZURE_BLOB, ...)
```

#### 51-60. Additional Cloud Patterns
- **51**: S3 event-triggered ETL
- **52**: Cloud data lake to warehouse
- **53**: Multi-region data replication
- **54**: Cloud backup and restore
- **55**: Serverless ETL with Lambda/Functions
- **56**: Cloud data archival
- **57**: Cross-account S3 access
- **58**: Cloud data encryption at rest
- **59**: Cloud cost optimization via compression
- **60**: Hybrid cloud synchronization

---

### Category 5: Complex Transformations (Cases 61-75)

#### 61. Time Series Analysis
```python
custom_code = """
# Convert to datetime
df['date'] = pd.to_datetime(df['date'])

# Set datetime index
df = df.set_index('date')

# Resample to daily/monthly
df_daily = df.resample('D').agg({
    'sales': 'sum',
    'orders': 'count',
    'customers': 'nunique'
})

# Calculate moving averages
df_daily['sales_ma7'] = df_daily['sales'].rolling(window=7).mean()
df_daily['sales_ma30'] = df_daily['sales'].rolling(window=30).mean()

# Calculate year-over-year growth
df_daily['sales_yoy'] = df_daily['sales'].pct_change(periods=365)

df = df_daily.reset_index()
"""
```

#### 62. Customer Segmentation (RFM Analysis)
```python
custom_code = """
from datetime import datetime

# Calculate RFM metrics
analysis_date = pd.Timestamp.now()

rfm = df.groupby('customer_id').agg({
    'order_date': lambda x: (analysis_date - x.max()).days,  # Recency
    'order_id': 'count',  # Frequency
    'amount': 'sum'  # Monetary
})

rfm.columns = ['recency', 'frequency', 'monetary']

# Create RFM scores (1-5)
rfm['r_score'] = pd.qcut(rfm['recency'], 5, labels=[5,4,3,2,1])
rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])
rfm['m_score'] = pd.qcut(rfm['monetary'], 5, labels=[1,2,3,4,5])

# Combined RFM score
rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)

# Segment customers
def segment_customer(score):
    r, f, m = int(score[0]), int(score[1]), int(score[2])
    
    if r >= 4 and f >= 4 and m >= 4:
        return 'Champions'
    elif r >= 3 and f >= 3:
        return 'Loyal Customers'
    elif r >= 4:
        return 'Potential Loyalists'
    elif f >= 4:
        return 'At Risk'
    else:
        return 'Lost'

rfm['segment'] = rfm['rfm_score'].apply(segment_customer)

df = rfm.reset_index()
"""
```

#### 63. Anomaly Detection
```python
custom_code = """
from scipy import stats

# Z-score method
z_scores = np.abs(stats.zscore(df['amount']))
df['is_anomaly'] = z_scores > 3

# IQR method
Q1 = df['amount'].quantile(0.25)
Q3 = df['amount'].quantile(0.75)
IQR = Q3 - Q1
df['is_outlier'] = (df['amount'] < (Q1 - 1.5 * IQR)) | (df['amount'] > (Q3 + 1.5 * IQR))

# Moving average deviation
df['ma'] = df['amount'].rolling(window=30).mean()
df['ma_std'] = df['amount'].rolling(window=30).std()
df['deviation'] = np.abs(df['amount'] - df['ma']) / df['ma_std']
df['is_spike'] = df['deviation'] > 3
"""
```

#### 64. Text Mining and NLP
```python
custom_code = """
import re
from collections import Counter

# Clean text
df['clean_text'] = df['description'].str.lower()
df['clean_text'] = df['clean_text'].str.replace(r'[^a-z\\s]', '', regex=True)

# Extract keywords
def extract_keywords(text, top_n=5):
    words = text.split()
    # Remove stopwords (simplified)
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}
    words = [w for w in words if w not in stopwords]
    
    # Get top keywords
    counter = Counter(words)
    return ', '.join([word for word, count in counter.most_common(top_n)])

df['keywords'] = df['clean_text'].apply(extract_keywords)

# Sentiment analysis (simplified)
positive_words = ['good', 'great', 'excellent', 'love', 'best']
negative_words = ['bad', 'poor', 'worst', 'hate', 'terrible']

def calculate_sentiment(text):
    words = text.split()
    pos_count = sum(1 for w in words if w in positive_words)
    neg_count = sum(1 for w in words if w in negative_words)
    return pos_count - neg_count

df['sentiment_score'] = df['clean_text'].apply(calculate_sentiment)
"""
```

#### 65. Geospatial Analysis
```python
custom_code = """
from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance between two points on Earth"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r

# Calculate distance from headquarters
hq_lat, hq_lon = 40.7128, -74.0060  # New York

df['distance_from_hq'] = df.apply(
    lambda row: haversine(hq_lon, hq_lat, row['longitude'], row['latitude']),
    axis=1
)

# Categorize by distance
df['distance_category'] = pd.cut(
    df['distance_from_hq'],
    bins=[0, 50, 200, 500, 10000],
    labels=['Local', 'Regional', 'National', 'International']
)
"""
```

#### 66-75. Additional Transformation Patterns
- **66**: Machine learning feature engineering
- **67**: Data normalization and standardization
- **68**: Missing value imputation strategies
- **69**: Categorical encoding (one-hot, label)
- **70**: Time-based feature extraction
- **71**: Cross-feature interactions
- **72**: Binning and discretization
- **73**: Principal component analysis (PCA)
- **74**: Data augmentation
- **75**: Custom business logic rules

---

### Category 6: Real-Time & Streaming (Cases 76-85)

#### 76. Kafka Consumer to Database
```python
custom_code = """
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'orders-topic',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

records = []
for message in consumer:
    records.append(message.value)
    
    if len(records) >= 1000:  # Batch size
        df = pd.DataFrame(records)
        break

df = pd.DataFrame(records)
"""
```

#### 77. Redis Cache to Database Sync
```python
source = DataSource(
    name="redis_source",
    source_type=SourceType.REDIS,
    connection_params={
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
)
```

#### 78. CDC (Change Data Capture) Simulation
```python
custom_code = """
# Track changes since last run
last_run_time = pd.Timestamp('2024-01-01')  # From metadata

# Filter for changes
df_changes = df[df['updated_at'] > last_run_time]

# Mark operation type
df_changes['operation'] = 'UPDATE'

# New records
df_new = df_changes[df_changes['created_at'] == df_changes['updated_at']]
df_new['operation'] = 'INSERT'

# Combine
df = pd.concat([df_changes, df_new]).drop_duplicates()
"""
```

#### 79-85. Additional Streaming Patterns
- **79**: WebSocket data stream processing
- **80**: IoT sensor data pipeline
- **81**: Log stream aggregation
- **82**: Real-time alerting pipeline
- **83**: Event sourcing to materialized views
- **84**: Micro-batch processing
- **85**: Stream-to-stream transformation

---

### Category 7: Data Quality & Governance (Cases 86-100)

#### 86. Data Profiling
```python
custom_code = """
# Generate data profile
profile = {
    'row_count': len(df),
    'column_count': len(df.columns),
    'null_counts': df.isnull().sum().to_dict(),
    'data_types': df.dtypes.astype(str).to_dict(),
    'unique_counts': df.nunique().to_dict(),
    'memory_usage': df.memory_usage(deep=True).sum(),
}

# Statistical summary
numeric_cols = df.select_dtypes(include=[np.number]).columns
for col in numeric_cols:
    profile[f'{col}_mean'] = df[col].mean()
    profile[f'{col}_std'] = df[col].std()
    profile[f'{col}_min'] = df[col].min()
    profile[f'{col}_max'] = df[col].max()

# Save profile
with open('/data/profile.json', 'w') as f:
    json.dump(profile, f, indent=2, default=str)
"""
```

#### 87. PII Detection and Masking
```python
custom_code = """
import re

def mask_email(email):
    if pd.isna(email):
        return email
    name, domain = email.split('@')
    return f"{name[0]}***@{domain}"

def mask_phone(phone):
    if pd.isna(phone):
        return phone
    return f"***-***-{phone[-4:]}"

def mask_ssn(ssn):
    if pd.isna(ssn):
        return ssn
    return f"***-**-{ssn[-4:]}"

# Apply masking
df['email_masked'] = df['email'].apply(mask_email)
df['phone_masked'] = df['phone'].apply(mask_phone)
df['ssn_masked'] = df['ssn'].apply(mask_ssn)

# Drop original sensitive columns
df = df.drop(['email', 'phone', 'ssn'], axis=1)
"""
```

#### 88. Data Lineage Tracking
```python
transformation = Transformation(
    name="add_lineage",
    transformation_type=TransformationType.CUSTOM_CODE,
    custom_code="""
# Add lineage metadata
df['_source_system'] = 'CRM_DB'
df['_extracted_at'] = pd.Timestamp.now()
df['_etl_job_id'] = '${job_id}'
df['_etl_run_id'] = '${run_id}'
df['_data_version'] = 1
"""
)
```

#### 89. Schema Validation
```python
custom_code = """
# Define expected schema
expected_schema = {
    'customer_id': 'int64',
    'email': 'object',
    'age': 'int64',
    'created_at': 'datetime64[ns]'
}

# Validate schema
for col, dtype in expected_schema.items():
    if col not in df.columns:
        raise ValueError(f"Missing column: {col}")
    
    if df[col].dtype != dtype:
        # Try to convert
        try:
            df[col] = df[col].astype(dtype)
        except:
            raise ValueError(f"Column {col} cannot be converted to {dtype}")
"""
```

#### 90-100. Final Patterns
- **90**: Duplicate detection across sources
- **91**: Reference data validation
- **92**: Business rule enforcement
- **93**: Data reconciliation reports
- **94**: Audit trail generation
- **95**: Data retention policy enforcement
- **96**: GDPR compliance (right to be forgotten)
- **97**: Data dictionary generation
- **98**: Metadata catalog updates
- **99**: Error data quarantine
- **100**: End-to-end data quality scorecard

---

## API Reference

### ETLManager

```python
manager = ETLManager(workspace_dir="./etl_workspace")
```

**Methods:**
- `create_job(job: ETLJob) -> str`: Create new ETL job
- `update_job(job: ETLJob)`: Update existing job
- `delete_job(job_id: str)`: Delete job
- `get_job(job_id: str) -> ETLJob`: Retrieve job
- `list_jobs() -> List[ETLJob]`: List all jobs
- `execute_job(job_id: str) -> ETLMetrics`: Execute job
- `get_job_metrics(job_id: str, limit: int) -> List[ETLMetrics]`: Get execution history

### DataSource

```python
source = DataSource(
    name="source_name",
    source_type=SourceType.DATABASE,
    connection_params={...},
    table="table_name",
    query="SELECT * FROM table",
    incremental_column="updated_at",
    incremental_value="2024-01-01",
    batch_size=10000,
    encrypted=True
)
```

### DataTarget

```python
target = DataTarget(
    name="target_name",
    target_type=TargetType.DATABASE,
    connection_params={...},
    table="table_name",
    write_mode="append",  # or "overwrite", "upsert"
    batch_size=10000,
    encrypted=True
)
```

### Transformation

```python
trans = Transformation(
    name="transform_name",
    transformation_type=TransformationType.CUSTOM_CODE,
    config={...},
    custom_code="df['new_col'] = df['old_col'] * 2",
    order=1,
    enabled=True
)
```

---

## Best Practices

### 1. Security
- Always use environment variables for credentials
- Enable encryption for sensitive connections
- Use HTTPS/TLS for API connections
- Implement principle of least privilege
- Regular security audits

### 2. Performance
- Use batch processing for large datasets
- Enable parallel execution when possible
- Optimize SQL queries
- Use appropriate file formats (Parquet for analytics)
- Implement incremental loading

### 3. Error Handling
- Set appropriate retry counts
- Implement idempotent operations
- Use transaction management
- Monitor error rates
- Set up alerting

### 4. Monitoring
- Track execution metrics
- Set up performance baselines
- Monitor resource usage
- Review audit logs regularly
- Create dashboards for visibility

### 5. Testing
- Test with sample data first
- Validate transformations
- Check data quality
- Test failure scenarios
- Document test cases

### 6. Documentation
- Document data sources and targets
- Explain transformation logic
- Maintain data dictionaries
- Version control configurations
- Keep runbooks updated

---

## Troubleshooting Guide

### Common Issues

**Issue 1: Connection Timeout**
```python
# Solution: Increase timeout
connection_params = {
    ...
    'timeout': 60  # Increase from default
}
```

**Issue 2: Memory Error**
```python
# Solution: Use chunking
source = DataSource(
    ...,
    batch_size=1000  # Reduce batch size
)
```

**Issue 3: Duplicate Data**
```python
# Solution: Add deduplication
Transformation(
    name="dedupe",
    transformation_type=TransformationType.DEDUPLICATE,
    config={'subset': ['id'], 'keep': 'last'}
)
```

---

## Support & Community

- Documentation: [docs.nexus-etl.com]
- GitHub: [github.com/nexus/etl]
- Community Forum: [forum.nexus-etl.com]
- Email: support@nexus-etl.com

---

# Nexus Enterprise ETL System - Setup Guide

## Installation

### 1. System Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB+ recommended for large datasets)
- 10GB disk space for workspace and logs
- Network access to data sources and targets

### 2. Python Dependencies

Create `requirements.txt`:

```txt
# Core dependencies
pandas>=1.5.0
numpy>=1.21.0
python-dateutil>=2.8.2

# Database drivers
psycopg2-binary>=2.9.0
mysql-connector-python>=8.0.0
pymongo>=4.0.0
redis>=4.3.0
elasticsearch>=8.0.0
cx-Oracle>=8.3.0
pyodbc>=4.0.0

# Cloud storage
boto3>=1.24.0
azure-storage-blob>=12.13.0
google-cloud-storage>=2.5.0

# API & networking
requests>=2.28.0
urllib3>=1.26.0
paramiko>=2.11.0

# Security & encryption
cryptography>=38.0.0
python-dotenv>=0.20.0

# Data formats
openpyxl>=3.0.0
pyarrow>=9.0.0
fastparquet>=0.8.0

# Scheduling & async
APScheduler>=3.9.0
asyncio>=3.4.3

# Kafka (optional)
kafka-python>=2.0.0

# Monitoring (optional)
prometheus-client>=0.14.0
```

### 3. Installation Steps

```bash
# Clone repository
git clone https://github.com/your-org/nexus-etl.git
cd nexus-etl

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 4. Environment Configuration

Create `.env` file:

```bash
# Master encryption key (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
MASTER_ENCRYPTION_KEY=your-encryption-key-here

# Database connections
PROD_DB_HOST=your-db-host
PROD_DB_USER=your-username
PROD_DB_PASSWORD=your-password

DW_HOST=your-warehouse-host
DW_USER=your-dw-user
DW_PASSWORD=your-dw-password

# AWS credentials
AWS_ACCESS_KEY=your-aws-access-key
AWS_SECRET_KEY=your-aws-secret-key
AWS_REGION=us-east-1

# Azure credentials
AZURE_STORAGE_ACCOUNT=your-storage-account
AZURE_STORAGE_KEY=your-storage-key

# Google Cloud
GCP_PROJECT_ID=your-project-id
GCP_CREDENTIALS_PATH=/path/to/service-account.json

# API tokens
SALESFORCE_TOKEN=your-salesforce-token
STRIPE_API_KEY=your-stripe-key
ENRICHMENT_API_KEY=your-enrichment-key

# Elasticsearch
ES_HOST=elasticsearch.company.com
ES_USER=elastic
ES_PASSWORD=your-es-password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
```

### 5. Directory Structure

```
nexus-etl/
├── etl_core.py                 # Main ETL engine
├── etl_examples.py             # Usage examples
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── .env.example               # Environment template
├── README.md                   # Documentation
├── etl_workspace/             # Working directory
│   ├── jobs/                  # Job configurations
│   ├── logs/                  # Execution logs
│   └── data/                  # Temporary data
├── config/                    # Configuration files
│   └── connections.yaml       # Connection definitions
├── tests/                     # Unit tests
│   ├── test_connectors.py
│   ├── test_transformations.py
│   └── test_security.py
└── scripts/                   # Utility scripts
    ├── generate_key.py
    └── test_connections.py
```

## Quick Start

### Example 1: Simple Database to File

```python
from etl_core import ETLManager, ETLJob, DataSource, DataTarget
from etl_core import SourceType, TargetType
import uuid

# Initialize manager
manager = ETLManager()

# Define source
source = DataSource(
    name="my_database",
    source_type=SourceType.DATABASE,
    connection_params={
        'type': 'postgresql',
        'host': 'localhost',
        'database': 'mydb',
        'user': 'postgres',
        'password': 'password'
    },
    table='users'
)

# Define target
target = DataTarget(
    name="csv_export",
    target_type=TargetType.FILE,
    connection_params={},
    file_path='./output/users.csv',
    file_format='csv'
)

# Create job
job = ETLJob(
    job_id=str(uuid.uuid4()),
    name="Export Users",
    description="Export users to CSV",
    sources=[source],
    transformations=[],
    targets=[target]
)

# Execute
job_id = manager.create_job(job)
metrics = manager.execute_job(job_id)

print(f"Status: {metrics.status.value}")
print(f"Rows: {metrics.rows_loaded}")
```

### Example 2: API to Database with Transformation

```python
from etl_core import Transformation, TransformationType

# Source: REST API
source = DataSource(
    name="api_source",
    source_type=SourceType.API,
    api_endpoint="https://api.example.com/data",
    api_method="GET",
    api_headers={'Authorization': 'Bearer TOKEN'}
)

# Transformation: Clean and enrich
transformation = Transformation(
    name="clean_data",
    transformation_type=TransformationType.CUSTOM_CODE,
    custom_code="""
# Clean email addresses
df['email'] = df['email'].str.lower().str.strip()

# Add timestamp
df['processed_at'] = pd.Timestamp.now()

# Calculate age from birthdate
df['age'] = (pd.Timestamp.now() - pd.to_datetime(df['birthdate'])).dt.days / 365.25
""",
    order=1
)

# Target: Database
target = DataTarget(
    name="database_target",
    target_type=TargetType.DATABASE,
    connection_params={
        'type': 'postgresql',
        'host': 'localhost',
        'database': 'warehouse',
        'user': 'etl_user',
        'password': 'password'
    },
    table='customers',
    write_mode='append'
)

# Create and execute job
job = ETLJob(
    job_id=str(uuid.uuid4()),
    name="API to Database",
    description="Load API data to warehouse",
    sources=[source],
    transformations=[transformation],
    targets=[target]
)

manager.create_job(job)
metrics = manager.execute_job(job.job_id)
```

## Security Best Practices

### 1. Credential Management

**Never hardcode credentials:**

```python
# ✗ BAD
connection_params = {
    'password': 'my-secret-password'
}

# ✓ GOOD
import os
connection_params = {
    'password': os.getenv('DB_PASSWORD')
}
```

### 2. Enable Encryption

```python
# Enable encryption for sensitive sources
source = DataSource(
    name="secure_source",
    source_type=SourceType.DATABASE,
    connection_params={...},
    encrypted=True  # Credentials will be encrypted
)
```

### 3. Use HTTPS/TLS

```python
# Always use HTTPS for APIs
source = DataSource(
    name="api_source",
    source_type=SourceType.API,
    api_endpoint="https://api.example.com",  # Not http://
    api_headers={
        'Authorization': f'Bearer {os.getenv("API_TOKEN")}'
    }
)
```

### 4. Audit Logging

All ETL operations are automatically logged. Review logs regularly:

```python
# Get execution history
metrics_list = manager.get_job_metrics(job_id, limit=10)

for metrics in metrics_list:
    print(f"Run: {metrics.run_id}")
    print(f"Status: {metrics.status.value}")
    print(f"Duration: {metrics.duration}s")
    if metrics.errors:
        print(f"Errors: {metrics.errors}")
```

## Advanced Configuration

### Connection Pooling

For high-performance scenarios with frequent database connections:

```python
from nexus.database.database_management import DatabaseFactory

# Create connection pool
pool_config = {
    'min_size': 5,
    'max_size': 20,
    'max_idle_time': 300
}

db_manager = DatabaseFactory.create_manager(
    'postgresql',
    connection_params,
    use_pool=True,
    pool_config=pool_config,
    singleton=True
)
```

### Caching

Enable multi-level caching for repeated queries:

```python
from nexus.database.enterprise_features import MultiLevelCache
import redis

# Setup cache
redis_client = redis.Redis(host='localhost', port=6379)
cache = MultiLevelCache(db, redis_client, l1_size=1000, ttl=300)

# Use cache
results = cache.get("SELECT * FROM customers WHERE status='active'")
```

### Parallel Processing

Enable parallel execution for independent transformations:

```python
job = ETLJob(
    job_id=str(uuid.uuid4()),
    name="Parallel Job",
    sources=[source],
    transformations=[transform1, transform2, transform3],
    targets=[target],
    parallel=True,
    max_workers=4
)
```

## Monitoring & Observability

### Metrics Dashboard

```python
# Get comprehensive metrics
metrics = manager.get_job_metrics(job_id)

for m in metrics:
    print(f"""
    Job: {m.job_id}
    Run: {m.run_id}
    Status: {m.status.value}
    Duration: {m.duration:.2f}s
    Extracted: {m.rows_extracted}
    Transformed: {m.rows_transformed}
    Loaded: {m.rows_loaded}
    Failed: {m.rows_failed}
    """)
```

### Health Checks

```python
# Test all connections before execution
def test_job_connections(job):
    from etl_core import ConnectorFactory, SecurityManager
    
    security = SecurityManager()
    
    # Test sources
    for source in job.sources:
        connector = ConnectorFactory.create_source_connector(source, security)
        is_healthy = connector.test_connection()
        print(f"Source '{source.name}': {'✓' if is_healthy else '✗'}")
    
    # Test targets
    for target in job.targets:
        connector = ConnectorFactory.create_target_connector(target, security)
        is_healthy = connector.test_connection()
        print(f"Target '{target.name}': {'✓' if is_healthy else '✗'}")
```

### Alerting

```python
job = ETLJob(
    ...,
    notifications={
        'on_failure': {
            'email': ['team@company.com'],
            'slack': ['#data-alerts']
        },
        'on_success': {
            'email': ['manager@company.com']
        }
    }
)
```

## Scheduling

### Cron-based Scheduling

```python
# Schedule job to run daily at 2 AM
job = ETLJob(
    ...,
    schedule="0 2 * * *"  # Cron expression
)

# Other examples:
# "0 * * * *"      - Every hour
# "0 */4 * * *"    - Every 4 hours
# "0 0 * * 0"      - Every Sunday at midnight
# "0 0 1 * *"      - First day of month at midnight
```

### Using APScheduler

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def run_etl_job(job_id):
    manager = ETLManager()
    metrics = manager.execute_job(job_id)
    print(f"Job {job_id} completed: {metrics.status.value}")

# Add jobs to scheduler
scheduler.add_job(
    run_etl_job,
    'cron',
    args=['job-001'],
    hour=2,
    minute=0
)

scheduler.start()
```

## Testing

### Unit Tests

Create `tests/test_etl.py`:

```python
import unittest
from etl_core import ETLManager, DataSource, SourceType

class TestETL(unittest.TestCase):
    
    def setUp(self):
        self.manager = ETLManager(workspace_dir="./test_workspace")
    
    def test_create_job(self):
        job = create_test_job()
        job_id = self.manager.create_job(job)
        self.assertIsNotNone(job_id)
    
    def test_source_connection(self):
        source = DataSource(
            name="test_db",
            source_type=SourceType.DATABASE,
            connection_params={
                'type': 'sqlite',
                'database': ':memory:'
            }
        )
        # Test connection logic
        
if __name__ == '__main__':
    unittest.main()
```

### Integration Tests

```python
def test_end_to_end_pipeline():
    # Create test data
    # Run pipeline
    # Verify output
    pass
```

## Troubleshooting

### Common Issues

**Issue 1: Import Error**
```
ModuleNotFoundError: No module named 'pandas'
```
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

**Issue 2: Connection Timeout**
```
Connection timeout to database
```
**Solution:** Increase timeout in connection params
```python
connection_params = {
    'timeout': 60  # Increase from default 10
}
```

**Issue 3: Memory Error**
```
MemoryError: Unable to allocate array
```
**Solution:** Reduce batch size
```python
source = DataSource(
    ...,
    batch_size=1000  # Reduce from 10000
)
```

**Issue 4: Permission Denied**
```
PermissionError: [Errno 13] Permission denied
```
**Solution:** Check file/directory permissions
```bash
chmod 755 ./etl_workspace
```

## Performance Tuning

### Database Query Optimization

```python
# Use indexes
source = DataSource(
    ...,
    query="""
        SELECT /*+ INDEX(orders idx_order_date) */
        * FROM orders
        WHERE order_date >= '2024-01-01'
    """
)

# Use LIMIT for testing
source = DataSource(
    ...,
    query="SELECT * FROM large_table LIMIT 10000"
)
```

### Batch Size Optimization

```python
# For small rows, use larger batches
source = DataSource(..., batch_size=50000)

# For large rows (with BLOBs), use smaller batches
source = DataSource(..., batch_size=100)
```

### Parallel Execution

```python
# Enable parallel processing
job = ETLJob(
    ...,
    parallel=True,
    max_workers=8  # Adjust based on CPU cores
)
```

## Production Deployment

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "etl_core.py"]
```

Build and run:

```bash
docker build -t nexus-etl:latest .
docker run -d \
    --name nexus-etl \
    -v ./etl_workspace:/app/etl_workspace \
    -e DB_PASSWORD=${DB_PASSWORD} \
    nexus-etl:latest
```

### Kubernetes Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nexus-etl
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: etl
        image: nexus-etl:latest
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: etl-secrets
              key: db-password
        volumeMounts:
        - name: workspace
          mountPath: /app/etl_workspace
      volumes:
      - name: workspace
        persistentVolumeClaim:
          claimName: etl-workspace-pvc
```

### Monitoring with Prometheus

```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
jobs_total = Counter('etl_jobs_total', 'Total ETL jobs executed')
jobs_failed = Counter('etl_jobs_failed', 'Failed ETL jobs')
job_duration = Histogram('etl_job_duration_seconds', 'Job execution duration')

# In ETL executor
with job_duration.time():
    metrics = executor.execute()
    jobs_total.inc()
    if metrics.status == ETLStatus.FAILED:
        jobs_failed.inc()

# Start metrics server
start_http_server(8000)
```

## Support

- Documentation: https://docs.nexus-etl.com
- GitHub Issues: https://github.com/nexus/etl/issues
- Email: support@nexus-etl.com
- Slack: #nexus-etl-support

## License

MIT License - See LICENSE file for details