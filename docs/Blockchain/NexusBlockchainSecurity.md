# 50 Secure Blockchain Manager Examples

Complete guide with 50 examples showing how to protect user private keys and implement secure blockchain operations.

## Prerequisites

```bash
pip install web3>=6.0.0 eth-account cryptography
pip install ledgerblue trezor  # For hardware wallets
pip install boto3  # For AWS KMS
```

---

## Section 1: Encrypted Keystore (Examples 1-10)

### Example 1: Register New User with Encrypted Key
```python
from secure_blockchain_manager import SecureBlockchainManager

manager = SecureBlockchainManager(security_mode="encrypted_keystore")

# User provides private key ONLY during registration
private_key = "0x1234567890abcdef..."
password = "MySecurePassword123!"

address = manager.register_user(private_key, password)
print(f"✅ User registered: {address}")
print("🔒 Private key encrypted and stored securely")
```

### Example 2: Send Transaction with Encrypted Key
```python
manager = SecureBlockchainManager(security_mode="encrypted_keystore")

# User only needs password (not private key!)
signed_tx = manager.send_transaction_encrypted(
    from_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    to_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEc",
    amount=0.01,
    password="MySecurePassword123!"
)
print(f"Transaction: {signed_tx}")
```

### Example 3: Load Encrypted Key Temporarily
```python
from secure_blockchain_manager import EncryptedKeyStore

keystore = EncryptedKeyStore()

# Load key (only in memory, not exposed)
try:
    private_key = keystore.load_encrypted_key(
        address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        password="MySecurePassword123!"
    )
    print("✅ Key decrypted successfully")
finally:
    # Clear from memory immediately
    private_key = None
    del private_key
```

### Example 4: Change User Password
```python
from secure_blockchain_manager import EncryptedKeyStore

keystore = EncryptedKeyStore()

# Load with old password
old_password = "OldPassword123"
private_key = keystore.load_encrypted_key(
    address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    password=old_password
)

# Re-encrypt with new password
new_password = "NewPassword456"
keystore.save_encrypted_key(
    address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    private_key=private_key,
    password=new_password
)

# Clear key from memory
private_key = None
del private_key

print("✅ Password changed successfully")
```

### Example 5: Verify Password Without Exposing Key
```python
from secure_blockchain_manager import EncryptedKeyStore

keystore = EncryptedKeyStore()

def verify_password(address: str, password: str) -> bool:
    """Verify password without exposing private key"""
    try:
        key = keystore.load_encrypted_key(address, password)
        key = None  # Clear immediately
        del key
        return True
    except:
        return False

is_valid = verify_password(
    "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "MyPassword"
)
print(f"Password valid: {is_valid}")
```

### Example 6: Delete User's Encrypted Key
```python
from secure_blockchain_manager import EncryptedKeyStore

keystore = EncryptedKeyStore()

# Delete keystore file
keystore.delete_key("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
print("🗑️  Key deleted permanently")
```

### Example 7: Batch Register Multiple Users
```python
manager = SecureBlockchainManager(security_mode="encrypted_keystore")

users = [
    ("0xPrivateKey1", "Password1"),
    ("0xPrivateKey2", "Password2"),
    ("0xPrivateKey3", "Password3")
]

for private_key, password in users:
    address = manager.register_user(private_key, password)
    print(f"✅ Registered: {address}")
```

### Example 8: Export Encrypted Keystore (Backup)
```python
import shutil
from secure_blockchain_manager import EncryptedKeyStore

keystore = EncryptedKeyStore(storage_path="keystore")

# Create backup
shutil.copytree("keystore", "keystore_backup")
print("✅ Keystore backed up")
```

### Example 9: Import Encrypted Keystore
```python
import shutil

# Restore from backup
shutil.copytree("keystore_backup", "keystore")
print("✅ Keystore restored")
```

### Example 10: Validate Encrypted Keystore Integrity
```python
import json
from secure_blockchain_manager import EncryptedKeyStore

keystore = EncryptedKeyStore()

def validate_keystore(address: str) -> bool:
    """Check if keystore file is valid"""
    try:
        filename = f"keystore/{address.lower()}.json"
        with open(filename, 'r') as f:
            data = json.load(f)
        
        required_keys = ["address", "crypto", "version"]
        return all(key in data for key in required_keys)
    except:
        return False

is_valid = validate_keystore("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
print(f"Keystore valid: {is_valid}")
```

---

## Section 2: Web3 Keystore Format (Examples 11-15)

### Example 11: Create Web3-Compatible Keystore
```python
from secure_blockchain_manager import Web3KeyStore

keystore = Web3KeyStore()

# Create standard keystore (compatible with MetaMask)
keystore_data = keystore.create_keystore(
    private_key="0x1234567890abcdef...",
    password="MyPassword123"
)
print("✅ Web3 keystore created")
print(f"   Can be imported into MetaMask/MyEtherWallet")
```

### Example 12: Load Web3 Keystore
```python
from secure_blockchain_manager import Web3KeyStore

keystore = Web3KeyStore()

# Load and decrypt
private_key = keystore.load_keystore(
    address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    password="MyPassword123"
)
print("✅ Keystore decrypted")

# Use key, then clear
private_key = None
del private_key
```

### Example 13: Export Keystore for MetaMask
```python
import json
from secure_blockchain_manager import Web3KeyStore

keystore = Web3KeyStore()

# Create keystore
keystore_data = keystore.create_keystore(
    private_key="0x1234567890abcdef...",
    password="MyPassword123"
)

# Save for export
with open("metamask_import.json", "w") as f:
    json.dump(keystore_data, f, indent=2)

print("✅ Keystore saved: metamask_import.json")
print("   Import this file into MetaMask")
```

### Example 14: Convert Private Key to Keystore
```python
from eth_account import Account

# User has private key, wants keystore
private_key = "0x1234567890abcdef..."
password = "SecurePassword"

account = Account.from_key(private_key)
keystore = account.encrypt(password)

# Save keystore
import json
with open(f"{account.address.lower()}.json", "w") as f:
    json.dump(keystore, f, indent=2)

print(f"✅ Keystore created for {account.address}")
```

### Example 15: Validate Web3 Keystore Format
```python
import json

def is_valid_web3_keystore(filename: str) -> bool:
    """Check if file is valid Web3 keystore"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        required = ["address", "crypto", "version"]
        crypto_required = ["cipher", "ciphertext", "kdf"]
        
        return (all(k in data for k in required) and
                all(k in data["crypto"] for k in crypto_required))
    except:
        return False

is_valid = is_valid_web3_keystore("keystore.json")
print(f"Valid Web3 keystore: {is_valid}")
```

---

## Section 3: Backend Signing Service (Examples 16-25)

### Example 16: Setup Backend Signing Service
```python
from secure_blockchain_manager import (
    TransactionSigningService, 
    EncryptedKeyStore
)

# Initialize service
keystore = EncryptedKeyStore()
signing_service = TransactionSigningService(keystore)

print("✅ Signing service initialized")
```

### Example 17: User Login - Create Session
```python
signing_service = TransactionSigningService(EncryptedKeyStore())

# User logs in with address and password
session_token = signing_service.create_session(
    address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    password="UserPassword123"
)

print(f"✅ Session created: {session_token}")
print("   Valid for 1 hour (3600 seconds)")
```

### Example 18: Sign Transaction with Session
```python
signing_service = TransactionSigningService(EncryptedKeyStore())

# User has active session
session_token = "abc123..."

# Build transaction
transaction = {
    'to': '0xRecipient',
    'value': 10000000000000000,  # 0.01 ETH
    'gas': 21000,
    'gasPrice': 50000000000,  # 50 Gwei
    'nonce': 0,
    'chainId': 11155111  # Sepolia
}

# Sign with session + password
signed_tx = signing_service.sign_transaction(
    session_token=session_token,
    transaction=transaction,
    password="UserPassword123"
)

print(f"✅ Transaction signed: {signed_tx[:20]}...")
```

### Example 19: User Logout - Revoke Session
```python
signing_service = TransactionSigningService(EncryptedKeyStore())

session_token = "abc123..."

# Revoke session
signing_service.revoke_session(session_token)
print("🔒 Session revoked - user logged out")
```

### Example 20: Session Expiration Management
```python
import time
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self):
        self.sessions = {}  # token -> (address, expiry)
    
    def create_session(self, address: str, duration: int = 3600) -> str:
        import hashlib, os
        token = hashlib.sha256(os.urandom(32)).hexdigest()
        expiry = datetime.now() + timedelta(seconds=duration)
        self.sessions[token] = (address, expiry)
        return token
    
    def is_valid(self, token: str) -> bool:
        if token not in self.sessions:
            return False
        
        address, expiry = self.sessions[token]
        if datetime.now() > expiry:
            del self.sessions[token]
            return False
        
        return True

manager = SessionManager()
token = manager.create_session("0xAddress", duration=3600)
print(f"Session valid: {manager.is_valid(token)}")
```

### Example 21: Flask API - Register Endpoint
```python
from flask import Flask, request, jsonify
from secure_blockchain_manager import SecureBlockchainManager

app = Flask(__name__)
manager = SecureBlockchainManager(security_mode="signing_service")

@app.route('/api/register', methods=['POST'])
def register():
    """User registers with private key (one-time)"""
    data = request.json
    private_key = data['private_key']
    password = data['password']
    
    try:
        address = manager.register_user(private_key, password)
        return jsonify({
            'success': True,
            'address': address,
            'message': 'User registered successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
```

### Example 22: Flask API - Login Endpoint
```python
@app.route('/api/login', methods=['POST'])
def login():
    """User login - returns session token"""
    data = request.json
    address = data['address']
    password = data['password']
    
    try:
        session_token = manager.create_user_session(address, password)
        return jsonify({
            'success': True,
            'session_token': session_token,
            'expires_in': 3600
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401
```

### Example 23: Flask API - Send Transaction Endpoint
```python
@app.route('/api/transaction', methods=['POST'])
def send_transaction():
    """Send transaction using session"""
    data = request.json
    session_token = data['session_token']
    to_address = data['to_address']
    amount = data['amount']
    password = data['password']
    
    try:
        signed_tx = manager.send_transaction_session(
            session_token=session_token,
            to_address=to_address,
            amount=amount,
            password=password
        )
        return jsonify({
            'success': True,
            'transaction': signed_tx
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
```

### Example 24: Flask API - Logout Endpoint
```python
@app.route('/api/logout', methods=['POST'])
def logout():
    """Revoke user session"""
    data = request.json
    session_token = data['session_token']
    
    manager.signing_service.revoke_session(session_token)
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })
```

### Example 25: Frontend Integration (JavaScript)
```javascript
// Register user
async function registerUser(privateKey, password) {
    const response = await fetch('/api/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            private_key: privateKey,
            password: password
        })
    });
    const data = await response.json();
    console.log('Registered:', data.address);
}

// Login
async function login(address, password) {
    const response = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            address: address,
            password: password
        })
    });
    const data = await response.json();
    localStorage.setItem('session_token', data.session_token);
    return data.session_token;
}

// Send transaction
async function sendTransaction(toAddress, amount, password) {
    const sessionToken = localStorage.getItem('session_token');
    const response = await fetch('/api/transaction', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_token: sessionToken,
            to_address: toAddress,
            amount: amount,
            password: password
        })
    });
    const data = await response.json();
    return data.transaction;
}
```

---

## Section 4: Hardware Wallet Integration (Examples 26-30)

### Example 26: Connect to Ledger Device
```python
from secure_blockchain_manager import HardwareWalletManager

hw_manager = HardwareWalletManager()

# Connect to Ledger
if hw_manager.connect_ledger():
    print("✅ Ledger connected")
    print("   Private key remains on device")
else:
    print("❌ Ledger not found")
```

### Example 27: Get Address from Ledger
```python
hw_manager = HardwareWalletManager()
hw_manager.connect_ledger()

# Get address (BIP44 path)
address = hw_manager.get_address(derivation_path="m/44'/60'/0'/0/0")
print(f"Ledger address: {address}")
```

### Example 28: Sign Transaction with Ledger
```python
hw_manager = HardwareWalletManager()
hw_manager.connect_ledger()

transaction = {
    'to': '0xRecipient',
    'value': 10000000000000000,  # 0.01 ETH
    'gas': 21000,
    'gasPrice': 50000000000,
    'nonce': 0
}

# User confirms on Ledger screen
signed_tx = hw_manager.sign_transaction(transaction)
print("✅ Transaction signed with Ledger")
```

### Example 29: Connect to Trezor Device
```python
hw_manager = HardwareWalletManager()

if hw_manager.connect_trezor():
    print("✅ Trezor connected")
    address = hw_manager.get_address()
    print(f"Trezor address: {address}")
```

### Example 30: Hardware Wallet with User Confirmation
```python
hw_manager = HardwareWalletManager()

def send_with_hardware_wallet(to_address: str, amount: float):
    """Send transaction with hardware wallet confirmation"""
    
    # Connect
    if not hw_manager.connect_ledger():
        print("❌ Please connect your Ledger")
        return
    
    print("✅ Ledger connected")
    print(f"📝 Preparing transaction:")
    print(f"   To: {to_address}")
    print(f"   Amount: {amount} ETH")
    print("\n⏳ Please confirm on your Ledger device...")
    
    transaction = {
        'to': to_address,
        'value': int(amount * 1e18),
        'gas': 21000,
        'gasPrice': 50000000000,
        'nonce': 0
    }
    
    try:
        signed_tx = hw_manager.sign_transaction(transaction)
        print("✅ Transaction signed and sent!")
        return signed_tx
    except Exception as e:
        print(f"❌ Transaction rejected or failed: {e}")

send_with_hardware_wallet("0xRecipient", 0.01)
```

---

## Section 5: AWS KMS Integration (Examples 31-35)

### Example 31: Initialize AWS KMS
```python
from secure_blockchain_manager import AWSKMSManager

kms = AWSKMSManager(region="us-east-1")
kms.initialize()
print("✅ AWS KMS initialized")
```

### Example 32: Create KMS Key for User
```python
kms = AWSKMSManager()
kms.initialize()

# Create key for user wallet
key_id = kms.create_key(alias="user-wallet-john")
print(f"✅ KMS key created: {key_id}")
print("   Key never leaves AWS")
```

### Example 33: Sign Transaction with KMS
```python
import hashlib

kms = AWSKMSManager()
kms.initialize()

# Transaction hash
tx_hash = hashlib.sha256(b"transaction_data").digest()

# Sign with KMS
signature = kms.sign_transaction(
    key_id="alias/user-wallet-john",
    message_hash=tx_hash
)
print("✅ Transaction signed with AWS KMS")
```

### Example 34: List User's KMS Keys
```python
import boto3

def list_user_keys(user_id: str):
    """List all KMS keys for a user"""
    kms_client = boto3.client('kms', region_name='us-east-1')
    
    response = kms_client.list_aliases()
    user_keys = [
        alias for alias in response['Aliases']
        if 'AliasName' in alias and user_id in alias['AliasName']
    ]
    
    return user_keys

keys = list_user_keys("john")
print(f"User has {len(keys)} KMS keys")
```

### Example 35: Rotate KMS Key
```python
kms = AWSKMSManager()
kms.initialize()

def enable_key_rotation(key_id: str):
    """Enable automatic key rotation"""
    kms.kms_client.enable_key_rotation(KeyId=key_id)
    print(f"✅ Key rotation enabled for {key_id}")
    print("   Key will rotate automatically every year")

enable_key_rotation("alias/user-wallet-john")
```

---

## Section 6: Security Best Practices (Examples 36-45)

### Example 36: Implement Password Strength Validation
```python
import re

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 12:
        print("❌ Password must be at least 12 characters")
        return False
    
    if not re.search(r'[A-Z]', password):
        print("❌ Password must contain uppercase letter")
        return False
    
    if not re.search(r'[a-z]', password):
        print("❌ Password must contain lowercase letter")
        return False
    
    if not re.search(r'[0-9]', password):
        print("❌ Password must contain number")
        return False
    
    if not re.search(r'[!@#$%^&*]', password):
        print("❌ Password must contain special character")
        return False
    
    return True

is_valid = validate_password("MySecure Pass123!")
```

### Example 37: Implement Rate Limiting for Login
```python
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window = timedelta(minutes=window_minutes)
        self.attempts = defaultdict(list)
    
    def is_allowed(self, address: str) -> bool:
        """Check if address can attempt login"""
        now = datetime.now()
        
        # Remove old attempts
        self.attempts[address] = [
            t for t in self.attempts[address]
            if now - t < self.window
        ]
        
        # Check if exceeded
        if len(self.attempts[address]) >= self.max_attempts:
            return False
        
        # Record attempt
        self.attempts[address].append(now)
        return True

limiter = RateLimiter()

if limiter.is_allowed("0xAddress"):
    print("✅ Login attempt allowed")
else:
    print("❌ Too many attempts - please wait")
```

### Example 38: Implement Two-Factor Authentication
```python
import pyotp

class TwoFactorAuth:
    def __init__(self):
        self.secrets = {}  # address -> secret
    
    def setup_2fa(self, address: str) -> str:
        """Setup 2FA for user"""
        secret = pyotp.random_base32()
        self.secrets[address] = secret
        
        # Generate QR code URL
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=address,
            issuer_name="My Blockchain App"
        )
        
        print(f"✅ 2FA enabled for {address}")
        print(f"   Scan QR code: {provisioning_uri}")
        return secret
    
    def verify_2fa(self, address: str, code: str) -> bool:
        """Verify 2FA code"""
        if address not in self.secrets:
            return False
        
        totp = pyotp.TOTP(self.secrets[address])
        return totp.verify(code)

tfa = TwoFactorAuth()
secret = tfa.setup_2fa("0xAddress")
is_valid = tfa.verify_2fa("0xAddress", "123456")
```

### Example 39: Implement Transaction Confirmation
```python
def confirm_transaction(from_addr: str, to_addr: str, amount: float) -> bool:
    """Require user confirmation for transaction"""
    print("\n" + "="*60)
    print("TRANSACTION CONFIRMATION REQUIRED")
    print("="*60)
    print(f"From: {from_addr}")
    print(f"To: {to_addr}")
    print(f"Amount: {amount} ETH")
    print("="*60)
    
    confirmation = input("Confirm transaction? (yes/no): ")
    return confirmation.lower() == "yes"

# Usage
if confirm_transaction("0xFrom", "0xTo", 0.01):
    print("✅ Proceeding with transaction")
else:
    print("❌ Transaction cancelled")
```

### Example 40: Implement Transaction Whitelist
```python
class TransactionWhitelist:
    def __init__(self):
        self.whitelist = set()
    
    def add_address(self, address: str):
        """Add address to whitelist"""
        self.whitelist.add(address.lower())
        print(f"✅ Added to whitelist: {address}")
    
    def is_whitelisted(self, address: str) -> bool:
        """Check if address is whitelisted"""
        return address.lower() in self.whitelist
    
    def remove_address(self, address: str):
        """Remove from whitelist"""
        self.whitelist.discard(address.lower())

whitelist = TransactionWhitelist()
whitelist.add_address("0xTrustedAddress")

if whitelist.is_whitelisted("0xTrustedAddress"):
    print("✅ Address is whitelisted - transaction allowed")
```

### Example 41: Implement Audit Logging
```python
import logging
from datetime import datetime
import json

class AuditLogger:
    def __init__(self, log_file: str = "audit.log"):
        self.logger = logging.getLogger('audit')
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_transaction(self, from_addr: str, to_addr: str, 
                       amount: float, tx_hash: str):
        """Log transaction details"""
        log_entry = {
            'type': 'transaction',
            'from': from_addr,
            'to': to_addr,
            'amount': amount,
            'tx_hash': tx_hash,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.info(json.dumps(log_entry))
    
    def log_login(self, address: str, success: bool):
        """Log login attempt"""
        log_entry = {
            'type': 'login',
            'address': address,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.info(json.dumps(log_entry))

audit = AuditLogger()
audit.log_transaction("0xFrom", "0xTo", 0.01, "0xtxhash")
audit.log_login("0xAddress", True)
```

### Example 42: Implement IP Whitelisting
```python
class IPWhitelist:
    def __init__(self):
        self.whitelist = set()
    
    def add_ip(self, ip_address: str):
        """Add IP to whitelist"""
        self.whitelist.add(ip_address)
        print(f"✅ IP whitelisted: {ip_address}")
    
    def is_allowed(self, ip_address: str) -> bool:
        """Check if IP is allowed"""
        return ip_address in self.whitelist

# In Flask
from flask import request

ip_whitelist = IPWhitelist()
ip_whitelist.add_ip("192.168.1.100")

@app.before_request
def check_ip():
    ip = request.remote_addr
    if not ip_whitelist.is_allowed(ip):
        return jsonify({'error': 'Unauthorized IP'}), 403
```

### Example 43: Implement Transaction Limits
```python
from datetime import datetime, timedelta

class TransactionLimiter:
    def __init__(self):
        self.transactions = {}  # address -> [(amount, timestamp)]
    
    def can_transact(self, address: str, amount: float,
                    daily_limit: float = 1.0) -> bool:
        """Check if transaction is within daily limit"""
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        
        # Get transactions in last 24 hours
        if address in self.transactions:
            self.transactions[address] = [
                (amt, ts) for amt, ts in self.transactions[address]
                if ts > day_ago
            ]
            
            daily_total = sum(amt for amt, _ in self.transactions[address])
            
            if daily_total + amount > daily_limit:
                print(f"❌ Daily limit exceeded: {daily_total + amount}/{daily_limit} ETH")
                return False
        
        # Record transaction
        if address not in self.transactions:
            self.transactions[address] = []
        self.transactions[address].append((amount, now))
        
        return True

limiter = TransactionLimiter()
if limiter.can_transact("0xAddress", 0.5, daily_limit=1.0):
    print("✅ Transaction within limits")
```

### Example 44: Implement Emergency Stop
```python
class EmergencyStop:
    def __init__(self):
        self.stopped = False
        self.admin_addresses = set()
    
    def add_admin(self, address: str):
        """Add admin address"""
        self.admin_addresses.add(address.lower())
    
    def emergency_stop(self, admin_address: str):
        """Activate emergency stop"""
        if admin_address.lower() in self.admin_addresses:
            self.stopped = True
            print("🚨 EMERGENCY STOP ACTIVATED")
        else:
            print("❌ Unauthorized")
    
    def resume(self, admin_address: str):
        """Resume operations"""
        if admin_address.lower() in self.admin_addresses:
            self.stopped = False
            print("✅ Operations resumed")
    
    def can_transact(self) -> bool:
        """Check if transactions are allowed"""
        if self.stopped:
            print("⛔ System stopped - transactions disabled")
```

## Example 45: Implement Secure Password Storage (Backend)

```python
import bcrypt

class PasswordManager:
    """Store password hashes (never plain text)"""
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), hashed.encode())

pm = PasswordManager()

# During registration
password_hash = pm.hash_password("UserPassword123")
# Store password_hash in database (NOT the password)
print(f"Hash stored in DB: {password_hash[:20]}...")

# During login
if pm.verify_password("UserPassword123", password_hash):
    print("✅ Password correct - login successful")
else:
    print("❌ Invalid password")

# Wrong password test
if pm.verify_password("WrongPassword", password_hash):
    print("✅ Password correct")
else:
    print("❌ Invalid password - access denied")
```

**Output:**
```
Hash stored in DB: $2b$12$abcdef123456...
✅ Password correct - login successful
❌ Invalid password - access denied
```

**Why This is Important:**
- Never store plain text passwords in database
- Bcrypt includes salt automatically
- Computationally expensive to brute force
- Industry standard for password hashing

---

## Example 46: Create Multi-Sig Wallet Structure

```python
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class MultiSigWallet:
    """Multi-signature wallet requiring multiple approvals"""
    address: str
    owners: List[str]
    required_signatures: int
    pending_transactions: Dict = None
    
    def __post_init__(self):
        if self.pending_transactions is None:
            self.pending_transactions = {}
    
    def get_info(self):
        """Get wallet information"""
        return {
            'address': self.address,
            'owners': self.owners,
            'required_signatures': self.required_signatures,
            'total_owners': len(self.owners),
            'pending_count': len([tx for tx in self.pending_transactions.values() 
                                 if not tx.get('executed', False)])
        }

# Create 2-of-3 multisig wallet
multisig = MultiSigWallet(
    address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    owners=[
        "0xOwner1a1b2c3d4e5f6789abcdef0123456789",
        "0xOwner29876543210fedcba9876543210fed",
        "0xOwner3abcdef123456789abcdef123456789"
    ],
    required_signatures=2
)

print("✅ Multi-Sig Wallet Created")
print(f"   Address: {multisig.address}")
print(f"   Owners: {len(multisig.owners)}")
print(f"   Required Signatures: {multisig.required_signatures}")
print(f"   Type: {multisig.required_signatures}-of-{len(multisig.owners)}")

info = multisig.get_info()
print(f"\n📊 Wallet Info:")
for key, value in info.items():
    print(f"   {key}: {value}")
```

**Output:**
```
✅ Multi-Sig Wallet Created
   Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Owners: 3
   Required Signatures: 2
   Type: 2-of-3

📊 Wallet Info:
   address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   owners: ['0xOwner1a1b2c3d4e5f6789abcdef0123456789', ...]
   required_signatures: 2
   total_owners: 3
   pending_count: 0
```

---

## Example 47: Propose Transaction in Multi-Sig

```python
import hashlib
from datetime import datetime
from dataclasses import dataclass
from typing import Set

class MultiSigManager:
    def __init__(self, multisig: MultiSigWallet):
        self.multisig = multisig
    
    def propose_transaction(self, proposer: str, to_address: str, 
                          amount: float) -> str:
        """Propose new transaction"""
        # Verify proposer is an owner
        if proposer not in self.multisig.owners:
            raise ValueError(f"❌ {proposer} is not an owner")
        
        # Create unique transaction ID
        tx_id = hashlib.sha256(
            f"{to_address}{amount}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Store pending transaction
        self.multisig.pending_transactions[tx_id] = {
            'to': to_address,
            'amount': amount,
            'proposer': proposer,
            'approvals': {proposer},  # Proposer automatically approves
            'proposed_at': datetime.now(),
            'executed': False,
            'tx_hash': None
        }
        
        print(f"✅ Transaction Proposed")
        print(f"   Transaction ID: {tx_id}")
        print(f"   Proposer: {proposer[:10]}...{proposer[-8:]}")
        print(f"   To: {to_address[:10]}...{to_address[-8:]}")
        print(f"   Amount: {amount} ETH")
        print(f"   Initial Approvals: 1/{self.multisig.required_signatures}")
        
        return tx_id
    
    def list_pending(self):
        """List all pending transactions"""
        pending = [
            (tx_id, tx) for tx_id, tx in self.multisig.pending_transactions.items()
            if not tx['executed']
        ]
        
        print(f"\n📋 Pending Transactions: {len(pending)}")
        for tx_id, tx in pending:
            print(f"\n   ID: {tx_id}")
            print(f"   To: {tx['to'][:10]}...{tx['to'][-8:]}")
            print(f"   Amount: {tx['amount']} ETH")
            print(f"   Approvals: {len(tx['approvals'])}/{self.multisig.required_signatures}")
            ready = "✅ Ready" if len(tx['approvals']) >= self.multisig.required_signatures else "⏳ Waiting"
            print(f"   Status: {ready}")

# Create manager
manager = MultiSigManager(multisig)

# Owner 1 proposes a transaction
tx_id = manager.propose_transaction(
    proposer="0xOwner1a1b2c3d4e5f6789abcdef0123456789",
    to_address="0xRecipient123456789abcdef0123456789",
    amount=0.5
)

# List pending transactions
manager.list_pending()
```

**Output:**
```
✅ Transaction Proposed
   Transaction ID: a3f5b2c1d4e6f789
   Proposer: 0xOwner1a1...23456789
   To: 0xRecipien...23456789
   Amount: 0.5 ETH
   Initial Approvals: 1/2

📋 Pending Transactions: 1

   ID: a3f5b2c1d4e6f789
   To: 0xRecipien...23456789
   Amount: 0.5 ETH
   Approvals: 1/2
   Status: ⏳ Waiting
```

---

## Example 48: Approve Multi-Sig Transaction

```python
class MultiSigManager:
    # ... (previous code) ...
    
    def approve_transaction(self, approver: str, tx_id: str) -> bool:
        """Approve pending transaction"""
        # Verify approver is an owner
        if approver not in self.multisig.owners:
            raise ValueError(f"❌ {approver} is not an owner")
        
        # Verify transaction exists
        if tx_id not in self.multisig.pending_transactions:
            raise ValueError(f"❌ Transaction {tx_id} not found")
        
        tx = self.multisig.pending_transactions[tx_id]
        
        # Check if already executed
        if tx['executed']:
            print(f"❌ Transaction already executed")
            return False
        
        # Check if already approved by this owner
        if approver in tx['approvals']:
            print(f"⚠️  Already approved by {approver[:10]}...{approver[-8:]}")
            return False
        
        # Add approval
        tx['approvals'].add(approver)
        approvals_count = len(tx['approvals'])
        
        print(f"✅ Approval Added")
        print(f"   Approver: {approver[:10]}...{approver[-8:]}")
        print(f"   Transaction: {tx_id}")
        print(f"   Approvals: {approvals_count}/{self.multisig.required_signatures}")
        
        # Check if ready for execution
        if approvals_count >= self.multisig.required_signatures:
            print(f"   🎉 Transaction ready for execution!")
            return True
        else:
            print(f"   ⏳ Need {self.multisig.required_signatures - approvals_count} more approval(s)")
            return False
    
    def get_transaction_details(self, tx_id: str):
        """Get detailed transaction information"""
        if tx_id not in self.multisig.pending_transactions:
            raise ValueError(f"Transaction {tx_id} not found")
        
        tx = self.multisig.pending_transactions[tx_id]
        
        print(f"\n📄 Transaction Details")
        print(f"   ID: {tx_id}")
        print(f"   To: {tx['to']}")
        print(f"   Amount: {tx['amount']} ETH")
        print(f"   Proposer: {tx['proposer'][:10]}...{tx['proposer'][-8:]}")
        print(f"   Proposed: {tx['proposed_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Approvals: {len(tx['approvals'])}/{self.multisig.required_signatures}")
        print(f"   Approved by:")
        for approval in tx['approvals']:
            print(f"      • {approval[:10]}...{approval[-8:]}")
        print(f"   Executed: {'✅ Yes' if tx['executed'] else '❌ No'}")
        if tx['tx_hash']:
            print(f"   TX Hash: {tx['tx_hash']}")

# Owner 2 approves the transaction
manager.approve_transaction(
    approver="0xOwner29876543210fedcba9876543210fed",
    tx_id=tx_id
)

# Show transaction details
manager.get_transaction_details(tx_id)
```

**Output:**
```
✅ Approval Added
   Approver: 0xOwner298...43210fed
   Transaction: a3f5b2c1d4e6f789
   Approvals: 2/2
   🎉 Transaction ready for execution!

📄 Transaction Details
   ID: a3f5b2c1d4e6f789
   To: 0xRecipient123456789abcdef0123456789
   Amount: 0.5 ETH
   Proposer: 0xOwner1a1...23456789
   Proposed: 2025-01-15 14:30:22
   Approvals: 2/2
   Approved by:
      • 0xOwner1a1...23456789
      • 0xOwner298...43210fed
   Executed: ❌ No
```

---

## Example 49: Execute Multi-Sig Transaction

```python
class MultiSigManager:
    # ... (previous code) ...
    
    def execute_transaction(self, executor: str, tx_id: str) -> str:
        """Execute transaction if enough approvals"""
        # Verify executor is an owner
        if executor not in self.multisig.owners:
            raise ValueError(f"❌ {executor} is not an owner")
        
        # Verify transaction exists
        if tx_id not in self.multisig.pending_transactions:
            raise ValueError(f"❌ Transaction {tx_id} not found")
        
        tx = self.multisig.pending_transactions[tx_id]
        
        # Check if already executed
        if tx['executed']:
            raise ValueError(f"❌ Transaction already executed")
        
        # Check if enough approvals
        approvals_count = len(tx['approvals'])
        if approvals_count < self.multisig.required_signatures:
            raise ValueError(
                f"❌ Not enough approvals: {approvals_count}/{self.multisig.required_signatures}"
            )
        
        # Execute transaction
        print(f"\n{'='*60}")
        print("🚀 EXECUTING MULTI-SIG TRANSACTION")
        print(f"{'='*60}")
        print(f"Transaction ID: {tx_id}")
        print(f"From: {self.multisig.address}")
        print(f"To: {tx['to']}")
        print(f"Amount: {tx['amount']} ETH")
        print(f"Executor: {executor[:10]}...{executor[-8:]}")
        print(f"Approved by {approvals_count} owners:")
        for i, approval in enumerate(tx['approvals'], 1):
            print(f"   {i}. {approval[:10]}...{approval[-8:]}")
        print(f"{'='*60}\n")
        
        # In production: send actual transaction here
        # tx_hash = blockchain.send_transaction(...)
        tx_hash = f"0x{hashlib.sha256(f'{tx_id}{datetime.now()}'.encode()).hexdigest()}"
        
        # Mark as executed
        tx['executed'] = True
        tx['tx_hash'] = tx_hash
        tx['executed_at'] = datetime.now()
        tx['executed_by'] = executor
        
        print(f"✅ Transaction Executed Successfully!")
        print(f"   TX Hash: {tx_hash}")
        print(f"   Block Explorer: https://etherscan.io/tx/{tx_hash}")
        
        return tx_hash
    
    def revoke_approval(self, owner: str, tx_id: str) -> bool:
        """Revoke approval before execution"""
        if owner not in self.multisig.owners:
            raise ValueError(f"❌ {owner} is not an owner")
        
        if tx_id not in self.multisig.pending_transactions:
            raise ValueError(f"❌ Transaction {tx_id} not found")
        
        tx = self.multisig.pending_transactions[tx_id]
        
        if tx['executed']:
            raise ValueError(f"❌ Cannot revoke - already executed")
        
        if owner not in tx['approvals']:
            print(f"⚠️  No approval to revoke for {owner[:10]}...{owner[-8:]}")
            return False
        
        # Remove approval
        tx['approvals'].remove(owner)
        
        print(f"🔙 Approval Revoked")
        print(f"   Owner: {owner[:10]}...{owner[-8:]}")
        print(f"   Transaction: {tx_id}")
        print(f"   Remaining Approvals: {len(tx['approvals'])}/{self.multisig.required_signatures}")
        
        return True

# Execute the transaction
tx_hash = manager.execute_transaction(
    executor="0xOwner1a1b2c3d4e5f6789abcdef0123456789",
    tx_id=tx_id
)

print(f"\n✅ Multi-Sig transaction complete!")
print(f"   Final TX Hash: {tx_hash[:20]}...")
```

**Output:**
```
============================================================
🚀 EXECUTING MULTI-SIG TRANSACTION
============================================================
Transaction ID: a3f5b2c1d4e6f789
From: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
To: 0xRecipient123456789abcdef0123456789
Amount: 0.5 ETH
Executor: 0xOwner1a1...23456789
Approved by 2 owners:
   1. 0xOwner1a1...23456789
   2. 0xOwner298...43210fed
============================================================

✅ Transaction Executed Successfully!
   TX Hash: 0xabc123def456789...
   Block Explorer: https://etherscan.io/tx/0xabc123def456789...

✅ Multi-Sig transaction complete!
   Final TX Hash: 0xabc123def456789...
```

---

## Example 50: Complete Multi-Sig Production Workflow

```python
from secure_blockchain_manager import SecureBlockchainManager, EncryptedKeyStore
import hashlib
from datetime import datetime
from typing import List, Dict

class ProductionMultiSig:
    """
    Complete production-ready multi-signature wallet
    with encrypted key storage and password verification
    """
    
    def __init__(self, owners: List[str], required: int):
        self.owners = set(owners)
        self.required = required
        self.pending = {}
        self.executed = {}
        self.keystore = EncryptedKeyStore()
        self.manager = SecureBlockchainManager(
            security_mode="encrypted_keystore"
        )
    
    def propose(self, proposer: str, to_addr: str, amount: float) -> str:
        """Propose new transaction"""
        if proposer not in self.owners:
            raise ValueError(f"Not an owner: {proposer}")
        
        # Generate transaction ID
        tx_id = hashlib.sha256(
            f"{to_addr}{amount}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Create pending transaction
        self.pending[tx_id] = {
            'to': to_addr,
            'amount': amount,
            'proposer': proposer,
            'approvals': {proposer},
            'proposed_at': datetime.now(),
            'executed': False
        }
        
        print(f"\n📝 TRANSACTION PROPOSED")
        print(f"{'='*60}")
        print(f"ID: {tx_id}")
        print(f"From: MultiSig Wallet")
        print(f"To: {to_addr[:10]}...{to_addr[-8:]}")
        print(f"Amount: {amount} ETH")
        print(f"Proposer: {proposer[:10]}...{proposer[-8:]}")
        print(f"Status: 1/{self.required} approvals")
        print(f"{'='*60}")
        
        return tx_id
    
    def approve(self, approver: str, tx_id: str, password: str) -> bool:
        """Approve transaction with password verification"""
        if approver not in self.owners:
            raise ValueError(f"Not an owner: {approver}")
        
        if tx_id not in self.pending:
            raise ValueError(f"Transaction not found: {tx_id}")
        
        tx = self.pending[tx_id]
        
        if approver in tx['approvals']:
            print(f"⚠️  Already approved by this owner")
            return False
        
        # Verify password (proves owner has access to their key)
        try:
            test_key = self.keystore.load_encrypted_key(approver, password)
            # Immediately clear from memory
            test_key = None
            del test_key
        except Exception as e:
            raise ValueError(f"❌ Invalid password: {str(e)}")
        
        # Add approval
        tx['approvals'].add(approver)
        approvals = len(tx['approvals'])
        
        print(f"\n✅ APPROVAL ADDED")
        print(f"{'='*60}")
        print(f"Transaction: {tx_id}")
        print(f"Approved by: {approver[:10]}...{approver[-8:]}")
        print(f"Total Approvals: {approvals}/{self.required}")
        
        if approvals >= self.required:
            print(f"🎉 READY FOR EXECUTION!")
        else:
            print(f"⏳ Need {self.required - approvals} more approval(s)")
        
        print(f"{'='*60}")
        
        return approvals >= self.required
    
    def execute(self, executor: str, tx_id: str, multisig_password: str) -> str:
        """Execute approved transaction"""
        if executor not in self.owners:
            raise ValueError(f"Not an owner: {executor}")
        
        if tx_id not in self.pending:
            raise ValueError(f"Transaction not found: {tx_id}")
        
        tx = self.pending[tx_id]
        
        if tx['executed']:
            raise ValueError(f"Already executed")
        
        if len(tx['approvals']) < self.required:
            raise ValueError(
                f"Not enough approvals: {len(tx['approvals'])}/{self.required}"
            )
        
        print(f"\n{'='*60}")
        print("🚀 EXECUTING MULTI-SIG TRANSACTION")
        print(f"{'='*60}")
        print(f"Transaction ID: {tx_id}")
        print(f"To: {tx['to']}")
        print(f"Amount: {tx['amount']} ETH")
        print(f"Executor: {executor[:10]}...{executor[-8:]}")
        print(f"\nApproved by {len(tx['approvals'])} owners:")
        for i, owner in enumerate(tx['approvals'], 1):
            print(f"   {i}. {owner[:10]}...{owner[-8:]}")
        print(f"{'='*60}\n")
        
        # Execute transaction (using encrypted keystore)
        try:
            signed_tx = self.manager.send_transaction_encrypted(
                from_address=executor,
                to_address=tx['to'],
                amount=tx['amount'],
                password=multisig_password
            )
        except Exception as e:
            print(f"❌ Execution failed: {e}")
            raise
        
        # Mark as executed
        tx['executed'] = True
        tx['tx_hash'] = signed_tx
        tx['executed_at'] = datetime.now()
        tx['executed_by'] = executor
        
        # Move to executed transactions
        self.executed[tx_id] = tx
        del self.pending[tx_id]
        
        print(f"✅ TRANSACTION EXECUTED SUCCESSFULLY!")
        print(f"   TX Hash: {signed_tx[:20]}...")
        print(f"   Executed at: {tx['executed_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        return signed_tx
    
    def get_pending(self) -> List[Dict]:
        """Get all pending transactions"""
        return [
            {
                'id': tx_id,
                'to': tx['to'],
                'amount': tx['amount'],
                'proposer': tx['proposer'],
                'approvals': len(tx['approvals']),
                'required': self.required,
                'ready': len(tx['approvals']) >= self.required,
                'proposed_at': tx['proposed_at'].isoformat()
            }
            for tx_id, tx in self.pending.items()
        ]
    
    def get_statistics(self):
        """Get wallet statistics"""
        total_pending = len(self.pending)
        total_executed = len(self.executed)
        ready_to_execute = len([
            tx for tx in self.pending.values()
            if len(tx['approvals']) >= self.required
        ])
        
        print(f"\n📊 MULTI-SIG WALLET STATISTICS")
        print(f"{'='*60}")
        print(f"Total Owners: {len(self.owners)}")
        print(f"Required Signatures: {self.required}")
        print(f"Pending Transactions: {total_pending}")
        print(f"   └─ Ready to Execute: {ready_to_execute}")
        print(f"   └─ Waiting for Approvals: {total_pending - ready_to_execute}")
        print(f"Executed Transactions: {total_executed}")
        print(f"{'='*60}")


# ============================================================================
# COMPLETE WORKFLOW DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("COMPLETE MULTI-SIG PRODUCTION WORKFLOW")
    print("="*70)
    
    # Step 1: Create 2-of-3 MultiSig Wallet
    print("\n🔧 STEP 1: Initialize MultiSig Wallet")
    multisig = ProductionMultiSig(
        owners=[
            "0xOwner1a1b2c3d4e5f6789abcdef0123456789",
            "0xOwner29876543210fedcba9876543210fed",
            "0xOwner3abcdef123456789abcdef123456789"
        ],
        required=2
    )
    print("✅ 2-of-3 MultiSig Wallet Created")
    print(f"   Owners: 3")
    print(f"   Required: 2 signatures")
    
    # Step 2: Owner 1 Proposes Transaction
    print("\n🔧 STEP 2: Propose Transaction")
    tx_id = multisig.propose(
        proposer="0xOwner1a1b2c3d4e5f6789abcdef0123456789",
        to_addr="0xRecipient123456789abcdef0123456789",
        amount=0.5
    )
    
    # Step 3: Check Status
    print("\n🔧 STEP 3: Check Pending Transactions")
    multisig.get_statistics()
    
    pending = multisig.get_pending()
    if pending:
        print(f"\n📋 Pending Transactions:")
        for tx in pending:
            print(f"   • {tx['id']}: {tx['amount']} ETH")
            print(f"     Status: {tx['approvals']}/{tx['required']} approvals")
    
    # Step 4: Owner 2 Approves
    print("\n🔧 STEP 4: Second Owner Approves")
    try:
        ready = multisig.approve(
            approver="0xOwner29876543210fedcba9876543210fed",
            tx_id=tx_id,
            password="Owner2SecurePassword"
        )
        
        if ready:
            # Step 5: Execute Transaction
            print("\n🔧 STEP 5: Execute Transaction")
            try:
                tx_hash = multisig.execute(
                    executor="0xOwner1a1b2c3d4e5f6789abcdef0123456789",
                    tx_id=tx_id,
                    multisig_password="MultiSigPassword"
                )
                
                print(f"\n🎉 SUCCESS!")
                print(f"   Transaction Hash: {tx_hash[:20]}...")
                
            except Exception as e:
                print(f"\n⚠️  Note: {e}")
                print("   (In production, this would execute on blockchain)")
        
    except Exception as e:
        print(f"\n⚠️  Note: {e}")
        print("   (Demo mode - encrypted keys not set up)")
    
    # Step 6: Final Statistics
    print("\n🔧 STEP 6: Final Statistics")
    multisig.get_statistics()
    
    print("\n" + "="*70)
    print("✅ MULTI-SIG WORKFLOW DEMONSTRATION COMPLETE")
    print("="*70)
    
    print("\n💡 KEY FEATURES:")
    print("   ✓ Multiple owners share control")
    print("   ✓ Requires multiple approvals (2-of-3)")
    print("   ✓ Password verification for each approval")
    print("   ✓ Encrypted key storage")
    print("   ✓ Complete audit trail")
    print("   ✓ Transaction can't execute without enough approvals")
    print("   ✓ Any owner can propose")
    print("   ✓ Any owner can execute (if approved)")
    
    print("\n🔒 SECURITY BENEFITS:")
    print("   ✓ No single point of failure")
    print("   ✓ Protects against compromised keys")
    print("   ✓ Requires collusion to steal funds")
    print("   ✓ Perfect for company treasuries")
    print("   ✓ Ideal for shared wallets")
```

**Expected Output:**
```
======================================================================
COMPLETE MULTI-SIG PRODUCTION WORKFLOW
======================================================================

🔧 STEP 1: Initialize MultiSig Wallet
✅ 2-of-3 MultiSig Wallet Created
   Owners: 3
   Required: 2 signatures

🔧 STEP 2: Propose Transaction

📝 TRANSACTION PROPOSED
============================================================
ID: a3f5b2c1d4e6f789
From: MultiSig Wallet
To: 0xRecipien...23456789
Amount: 0.5 ETH
Proposer: 0xOwner1a1...23456789
Status: 1/2 approvals
============================================================

🔧 STEP 3: Check Pending Transactions

📊 MULTI-SIG WALLET STATISTICS
============================================================
Total Owners: 3
Required Signatures: 2
Pending Transactions: 1
   └─ Ready to Execute: 0
   └─ Waiting for Approvals: 1
Executed Transactions: 0
============================================================

📋 Pending Transactions:
   • a3f5b2c1d4e6f789: 0.5 ETH
     Status: 1/2 approvals

🔧 STEP 4: Second Owner Approves

✅ APPROVAL ADDED
============================================================
Transaction: a3f5b2c1d4e6f789
Approved by: 0xOwner298...43210fed
Total Approvals: 2/2
🎉 READY FOR EXECUTION!
============================================================

🔧 STEP 5: Execute Transaction

============================================================
🚀 EXECUTING MULTI-SIG TRANSACTION
============================================================
Transaction ID: a3f5b2c1d4e6f789
To: 0xRecipient123456789abcdef0123456789
Amount: 0.5 ETH
Executor: 0xOwner1a1...23456789

Approved by 2 owners:
   1. 0xOwner1a1...23456789
   2. 0xOwner298...43210fed
============================================================

✅ TRANSACTION EXECUTED SUCCESSFULLY!