# 20 Database Integration Examples

Complete examples for using the database-integrated blockchain manager with encrypted storage.

## Prerequisites

```bash
pip install web3>=6.0.0 eth-account python-dotenv requests
pip install psycopg2-binary cryptography sqlalchemy
```

---

## Example 1: Initialize Database Connection

```python
from database_manager import DatabaseManager

# Master database configuration
master_db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'your_db_password'
}

# Initialize database manager
db = DatabaseManager(master_db_config)
print("✅ Database manager initialized")
```

---

## Example 2: Create and Connect to User Database

```python
db = DatabaseManager(master_db_config)

# User credentials
user_email = "alice@example.com"
user_password = "SecurePassword123!"

# Connect (creates database if doesn't exist)
if db.connect_user_database(user_email, user_password):
    print(f"✅ Connected to encrypted database")
    print(f"   Database name: {db.user_db_name}")
else:
    print("❌ Connection failed")
```

**Output:**
```
✅ Connected to encrypted database
   Database name: user_db_a3f5b2c1d4e6f789abcdef0123456789
```

---

## Example 3: Save Encrypted Wallet

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

# Wallet details
wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
private_key = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

# Save wallet (private key is encrypted)
wallet_id = db.save_wallet(
    user_email="alice@example.com",
    address=wallet_address,
    private_key=private_key,
    chain_type="ethereum_sepolia",
    label="My Main Wallet"
)

print(f"✅ Wallet saved with ID: {wallet_id}")
print(f"   Private key encrypted with user password")
```

---

## Example 4: Retrieve Decrypted Private Key

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

# Retrieve private key (automatically decrypted)
wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
private_key = db.get_wallet_private_key(wallet_address)

print(f"✅ Private key retrieved and decrypted")
print(f"   Key: {private_key[:20]}...")

# Use the key for transactions
# Key is only in memory, never stored in plain text
```

---

## Example 5: Save Transaction to Database

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

# Transaction data
tx_data = {
    'tx_hash': '0xabc123def456789abc123def456789abc123def456789abc123def456789abc12',
    'from_address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
    'to_address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEc',
    'amount': 0.01,
    'chain_type': 'ethereum_sepolia',
    'status': 'pending',
    'gas_used': 21000,
    'gas_price': 50000000000,  # 50 Gwei
    'gas_cost': 0.00105
}

# Save to database
tx_id = db.save_transaction(tx_data)
print(f"✅ Transaction saved with ID: {tx_id}")
```

---

## Example 6: Get Transaction History

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

# Get all transactions
history = db.get_transaction_history("alice@example.com")

print(f"📊 Transaction History: {len(history)} transactions")
for tx in history[:5]:  # Show first 5
    print(f"\n   TX Hash: {tx['tx_hash'][:20]}...")
    print(f"   From: {tx['from_address'][:10]}...")
    print(f"   To: {tx['to_address'][:10]}...")
    print(f"   Amount: {tx['amount']} ETH")
    print(f"   Status: {tx['status']}")
    print(f"   Date: {tx['created_at']}")
```

**Output:**
```
📊 Transaction History: 3 transactions

   TX Hash: 0xabc123def456789ab...
   From: 0x742d35C...
   To: 0x742d35C...
   Amount: 0.01 ETH
   Status: confirmed
   Date: 2025-01-15 14:30:22
```

---

## Example 7: Filter Transaction History by Chain

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

# Get only Ethereum Sepolia transactions
sepolia_txs = db.get_transaction_history(
    user_email="alice@example.com",
    chain_type="ethereum_sepolia"
)

print(f"Ethereum Sepolia transactions: {len(sepolia_txs)}")

# Get only Polygon Amoy transactions
polygon_txs = db.get_transaction_history(
    user_email="alice@example.com",
    chain_type="polygon_amoy"
)

print(f"Polygon Amoy transactions: {len(polygon_txs)}")
```

---

## Example 8: Save Transaction Limits

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

# Define limits
limits = {
    'max_gas_price': 50.0,  # Max 50 Gwei
    'max_gas_limit': 300000,  # Max 300k gas
    'max_total_cost': 0.01,  # Max 0.01 ETH per transaction
    'max_priority_fee': 5.0,  # Max 5 Gwei priority fee
    'daily_limit': 1.0  # Max 1 ETH per day
}

# Save to database
if db.save_transaction_limits("alice@example.com", limits):
    print("✅ Transaction limits saved")
    print(f"   Max gas price: {limits['max_gas_price']} Gwei")
    print(f"   Max total cost: {limits['max_total_cost']} ETH")
    print(f"   Daily limit: {limits['daily_limit']} ETH")
```

---

## Example 9: Retrieve Transaction Limits

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

# Get limits from database
limits = db.get_transaction_limits("alice@example.com")

if limits:
    print("📊 Current Transaction Limits:")
    print(f"   Max gas price: {limits.get('max_gas_price')} Gwei")
    print(f"   Max gas limit: {limits.get('max_gas_limit')} units")
    print(f"   Max total cost: {limits.get('max_total_cost')} ETH")
    print(f"   Daily limit: {limits.get('daily_limit')} ETH")
else:
    print("No limits set")
```

---

## Example 10: Change Password (Re-encrypts All Data)

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "OldPassword123")

# Change password
old_password = "OldPassword123"
new_password = "NewSecurePassword456!"

print("🔄 Changing password and re-encrypting data...")

if db.change_password("alice@example.com", old_password, new_password):
    print("✅ Password changed successfully")
    print("   All wallets re-encrypted with new password")
    print("   All data remains accessible")
else:
    print("❌ Password change failed")
```

**What happens:**
1. Verifies old password
2. Retrieves all encrypted wallets
3. Decrypts with old password
4. Re-encrypts with new password
5. Updates password hash and salt
6. Commits all changes atomically

---

## Example 11: Complete Workflow - Register User and Save Wallet

```python
from database_manager import DatabaseManager
from eth_account import Account

# Initialize
db = DatabaseManager(master_db_config)

# User registration
user_email = "bob@example.com"
user_password = "BobSecure123!"

print("1. Creating user database...")
db_name = db.create_user_database(user_email)
print(f"   ✅ Database created: {db_name}")

print("\n2. Connecting to database...")
db.connect_user_database(user_email, user_password)
print("   ✅ Connected")

print("\n3. Generating new wallet...")
account = Account.create()
wallet_address = account.address
private_key = account.key.hex()
print(f"   ✅ Address: {wallet_address}")

print("\n4. Saving encrypted wallet...")
wallet_id = db.save_wallet(
    user_email=user_email,
    address=wallet_address,
    private_key=private_key,
    chain_type="ethereum_sepolia",
    label="Primary Wallet"
)
print(f"   ✅ Wallet ID: {wallet_id}")

print("\n5. Verifying wallet retrieval...")
retrieved_key = db.get_wallet_private_key(wallet_address)
assert retrieved_key == private_key
print("   ✅ Wallet can be decrypted successfully")
```

---

## Example 12: Save Multiple Wallets for Different Chains

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

wallets = [
    {
        'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        'private_key': '0xabc123...',
        'chain_type': 'ethereum_sepolia',
        'label': 'Ethereum Testnet'
    },
    {
        'address': '0x8f2c4d9e3b5a1f7c8d6e4a9b2c5f8e3d1a7b9c4e',
        'private_key': '0xdef456...',
        'chain_type': 'polygon_amoy',
        'label': 'Polygon Testnet'
    },
    {
        'address': '0x1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t',
        'private_key': '0xghi789...',
        'chain_type': 'ethereum',
        'label': 'Ethereum Mainnet'
    }
]

for wallet in wallets:
    wallet_id = db.save_wallet(
        user_email="alice@example.com",
        address=wallet['address'],
        private_key=wallet['private_key'],
        chain_type=wallet['chain_type'],
        label=wallet['label']
    )
    print(f"✅ Saved {wallet['label']}: ID {wallet_id}")
```

---

## Example 13: Integrated Transaction Flow

```python
from database_manager import DatabaseManager
from blockchain_manager import BlockchainManager, ChainType

# Initialize both managers
db = DatabaseManager(master_db_config)
blockchain = BlockchainManager()

# Connect
user_email = "alice@example.com"
user_password = "SecurePassword123!"
db.connect_user_database(user_email, user_password)
blockchain.connect(ChainType.ETHEREUM_SEPOLIA)

# Get wallet private key from database
wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
private_key = db.get_wallet_private_key(wallet_address)

# Send transaction
tx = blockchain.send_transaction(
    from_address=wallet_address,
    to_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEc",
    amount=0.001,
    private_key=private_key
)

# Save to database
tx_data = {
    'tx_hash': tx.tx_hash,
    'from_address': tx.from_address,
    'to_address': tx.to_address,
    'amount': tx.amount,
    'chain_type': tx.chain.value,
    'status': tx.status
}
tx_id = db.save_transaction(tx_data)

print(f"✅ Transaction sent and saved")
print(f"   TX Hash: {tx.tx_hash}")
print(f"   Database ID: {tx_id}")
```

---

## Example 14: Batch Transaction History Export

```python
import csv
from datetime import datetime

db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

# Get all transactions
history = db.get_transaction_history("alice@example.com")

# Export to CSV
filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

with open(filename, 'w', newline='') as f:
    if history:
        writer = csv.DictWriter(f, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)
        print(f"✅ Exported {len(history)} transactions to {filename}")
    else:
        print("No transactions to export")
```

---

## Example 15: Check Wallet Existence Before Saving

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

# Try to retrieve wallet
try:
    private_key = db.get_wallet_private_key(wallet_address)
    print(f"✅ Wallet already exists: {wallet_address}")
    print("   No need to save again")
except ValueError:
    print(f"Wallet not found, creating new one...")
    # Generate or import wallet
    private_key = "0x1234..."
    wallet_id = db.save_wallet(
        user_email="alice@example.com",
        address=wallet_address,
        private_key=private_key,
        chain_type="ethereum_sepolia"
    )
    print(f"✅ New wallet saved with ID: {wallet_id}")
```

---

## Example 16: Update Transaction Status

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

# Update transaction status after confirmation
with db.user_engine.connect() as conn:
    from sqlalchemy import text
    
    tx_hash = "0xabc123..."
    
    conn.execute(text("""
        UPDATE transactions
        SET status = 'confirmed',
            confirmed_at = CURRENT_TIMESTAMP,
            block_number = :block_number
        WHERE tx_hash = :tx_hash
    """), {
        "tx_hash": tx_hash,
        "block_number": 12345678
    })
    
    conn.commit()
    print(f"✅ Transaction {tx_hash[:20]}... marked as confirmed")
```

---

## Example 17: Get Transaction Statistics

```python
db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

with db.user_engine.connect() as conn:
    from sqlalchemy import text
    
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_transactions,
            SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(amount) as total_amount,
            AVG(gas_cost) as avg_gas_cost
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        WHERE u.email = :email
    """), {"email": "alice@example.com"})
    
    stats = result.fetchone()
    
    print("📊 Transaction Statistics:")
    print(f"   Total: {stats[0]}")
    print(f"   Confirmed: {stats[1]}")
    print(f"   Pending: {stats[2]}")
    print(f"   Failed: {stats[3]}")
    print(f"   Total Amount: {stats[4]} ETH")
    print(f"   Avg Gas Cost: {stats[5]:.6f} ETH")
```

---

## Example 18: Multi-User Database Management

```python
db = DatabaseManager(master_db_config)

users = [
    ("alice@example.com", "AlicePass123!"),
    ("bob@example.com", "BobPass456!"),
    ("charlie@example.com", "CharliePass789!")
]

for email, password in users:
    print(f"\n📧 Setting up {email}...")
    
    # Create/connect to user database
    if db.connect_user_database(email, password):
        print(f"   ✅ Database ready: {db.user_db_name}")
        
        # Initialize with default limits
        limits = {
            'max_gas_price': 100.0,
            'max_total_cost': 0.1,
            'max_gas_limit': 500000
        }
        db.save_transaction_limits(email, limits)
        print(f"   ✅ Default limits set")
```

---

## Example 19: Database Backup and Restore Simulation

```python
import json

db = DatabaseManager(master_db_config)
db.connect_user_database("alice@example.com", "SecurePassword123!")

# Export user data (encrypted)
with db.user_engine.connect() as conn:
    from sqlalchemy import text
    
    # Get all wallets (still encrypted)
    result = conn.execute(text("""
        SELECT address, encrypted_keystore, chain_type, label
        FROM wallets w
        JOIN users u ON w.user_id = u.id
        WHERE u.email = :email
    """), {"email": "alice@example.com"})
    
    wallets_backup = [dict(row._mapping) for row in result]
    
    # Get transaction history
    result = conn.execute(text("""
        SELECT tx_hash, from_address, to_address, amount, chain_type, status
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        WHERE u.email = :email
    """), {"email": "alice@example.com"})
    
    transactions_backup = [dict(row._mapping) for row in result]

# Save backup
backup_data = {
    'wallets': wallets_backup,
    'transactions': transactions_backup,
    'timestamp': datetime.now().isoformat()
}

with open('user_backup.json', 'w') as f:
    json.dump(backup_data, f, indent=2, default=str)

print(f"✅ Backup created")
print(f"   Wallets: {len(wallets_backup)}")
print(f"   Transactions: {len(transactions_backup)}")
print("   Note: Wallet data is still encrypted")
```

---

## Example 20: Complete Production Workflow

```python
from database_manager import DatabaseManager
from blockchain_manager import BlockchainManager, ChainType, TransactionLimits
from eth_account import Account
import os

def production_workflow():
    """Complete production workflow with database integration"""
    
    # Configuration
    master_db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    user_email = "production@example.com"
    user_password = os.getenv('USER_PASSWORD')
    
    print("="*70)
    print("PRODUCTION WORKFLOW WITH DATABASE INTEGRATION")
    print("="*70)
    
    # Step 1: Initialize managers
    print("\n1. Initializing...")
    db = DatabaseManager(master_db_config)
    blockchain = BlockchainManager()
    
    # Step 2: Connect to encrypted database
    print("\n2. Connecting to encrypted database...")
    if not db.connect_user_database(user_email, user_password):
        print("❌ Connection failed")
        return
    print(f"   ✅ Connected: {db.user_db_name}")
    
    # Step 3: Set transaction limits
    print("\n3. Configuring transaction limits...")
    limits = {
        'max_gas_price': 100.0,
        'max_total_cost': 0.05,
        'max_gas_limit': 500000,
        'daily_limit': 1.0
    }
    db.save_transaction_limits(user_email, limits)
    print("   ✅ Limits saved to database")
    
    # Step 4: Check for existing wallet or create new
    print("\n4. Setting up wallet...")
    wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    
    try:
        private_key = db.get_wallet_private_key(wallet_address)
        print(f"   ✅ Existing wallet loaded")
    except ValueError:
        print("   Creating new wallet...")
        account = Account.create()
        wallet_address = account.address
        private_key = account.key.hex()
        
        db.save_wallet(
            user_email=user_email,
            address=wallet_address,
            private_key=private_key,
            chain_type="ethereum_sepolia",
            label="Production Wallet"
        )
        print(f"   ✅ New wallet created and encrypted")
    
    # Step 5: Connect to blockchain
    print("\n5. Connecting to blockchain...")
    blockchain.connect(ChainType.ETHEREUM_SEPOLIA)
    
    # Apply limits from database
    db_limits = db.get_transaction_limits(user_email)
    if db_limits:
        blockchain.set_transaction_limits(TransactionLimits(
            max_gas_price=float(db_limits.get('max_gas_price', 100)),
            max_total_cost=float(db_limits.get('max_total_cost', 0.05))
        ))
        print("   ✅ Limits applied from database")
    
    # Step 6: Check balance
    print("\n6. Checking balance...")
    try:
        balance = blockchain.get_balance(wallet_address)
        print(f"   Balance: {balance:.6f} ETH")
    except Exception as e:
        print(f"   ⚠️  Could not fetch balance: {e}")
    
    # Step 7: Get transaction history from database
    print("\n7. Loading transaction history...")
    history = db.get_transaction_history(user_email, chain_type="ethereum_sepolia")
    print(f"   ✅ Found {len(history)} transactions in database")
    
    # Step 8: Estimate new transaction
    print("\n8. Estimating transaction cost...")
    estimate = blockchain.estimate_transaction_cost(
        "transfer",
        from_address=wallet_address,
        to_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEc",
        amount=0.001
    )
    print(f"   Gas: {estimate.estimated_gas} @ {estimate.recommended_gas_price:.2f} Gwei")
    print(f"   Cost: {estimate.total_cost_native:.6f} ETH")
    print(f"   Within limits: {'✅' if not estimate.will_exceed_limits else '❌'}")
    
    print("\n" + "="*70)
    print("✅ PRODUCTION WORKFLOW COMPLETE")
    print("="*70)
    print("\nKey Features Active:")
    print("  ✓ Encrypted database per user")
    print("  ✓ Password-protected wallet storage")
    print("  ✓ Transaction history tracking")
    print("  ✓ Limit enforcement from database")
    print("  ✓ Automatic re-encryption on password change")

if __name__ == "__main__":
    production_workflow()
```

---

## Summary

These 20 examples demonstrate:

1. **Database Initialization** (1-2) - Setup and connection
2. **Wallet Management** (3-4, 11-12, 15) - Encrypted storage and retrieval
3. **Transaction Tracking** (5-7, 14, 16-17) - Complete history
4. **Security Features** (8-10) - Limits and password changes
5. **Integration** (13, 20) - Combining blockchain with database
6. **Multi-User** (18) - Managing multiple users
7. **Production Workflow** (20) - Complete real-world example

All data is encrypted with the user's password and automatically re-encrypted when the password changes.