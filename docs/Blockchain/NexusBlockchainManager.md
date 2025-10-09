# 100 Usage Examples - Production Blockchain Manager

Complete guide with 100 real-world examples for the Production-Ready Multi-Chain Blockchain Manager.

## Prerequisites

```bash
pip install web3>=6.0.0 eth-account python-dotenv requests
```

Create `.env` file:
```bash
SEPOLIA_RPC_URL=https://rpc.sepolia.org
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
POLYGON_RPC_URL=https://polygon-rpc.com
AMOY_RPC_URL=https://rpc-amoy.polygon.technology
WALLET_PRIVATE_KEY=your_private_key_here
COINGECKO_API_KEY=your_api_key
```

---

## Section 1: Initialization & Configuration (1-10)

### Example 1: Basic Initialization
```python
from blockchain_manager import BlockchainManager

manager = BlockchainManager()
print("✅ Manager initialized")
```

### Example 2: Initialize with Transaction Limits
```python
from blockchain_manager import BlockchainManager, TransactionLimits

manager = BlockchainManager()
limits = TransactionLimits(
    max_gas_price=50.0,
    max_total_cost=0.01,
    max_gas_limit=300000
)
manager.set_transaction_limits(limits)
print("✅ Limits set")
```

### Example 3: Get Current Transaction Limits
```python
manager = BlockchainManager()
limits = manager.get_transaction_limits()
print(f"Max gas price: {limits.max_gas_price} Gwei")
print(f"Max total cost: {limits.max_total_cost}")
```

### Example 4: Update Transaction Limits
```python
manager = BlockchainManager()
new_limits = TransactionLimits(
    max_gas_price=100.0,
    max_total_cost=0.05
)
manager.set_transaction_limits(new_limits)
```

### Example 5: List All Supported Chains
```python
manager = BlockchainManager()
chains = manager.get_supported_chains()
for chain in chains:
    print(f"• {chain.value}")
```

### Example 6: List Only Testnets
```python
manager = BlockchainManager()
testnets = manager.list_testnets()
for testnet in testnets:
    print(f"🧪 {testnet.value}")
```

### Example 7: List Only Mainnets
```python
manager = BlockchainManager()
mainnets = manager.list_mainnets()
for mainnet in mainnets:
    print(f"🌐 {mainnet.value}")
```

### Example 8: Get Network Configuration
```python
from blockchain_manager import ChainType

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
config = manager.get_network_config()
print(f"Chain ID: {config.chain_id}")
print(f"RPC: {config.rpc_url}")
print(f"Explorer: {config.explorer_url}")
```

### Example 9: Check if Current Chain is Testnet
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
is_test = manager.is_testnet()
print(f"Is testnet: {is_test}")
```

### Example 10: Get Faucet URL for Testnet
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
faucet = manager.get_faucet_url()
print(f"Get free tokens: {faucet}")
```

---

## Section 2: Network Connections (11-20)

### Example 11: Connect to Ethereum Mainnet
```python
from blockchain_manager import ChainType

manager = BlockchainManager()
success = manager.connect(ChainType.ETHEREUM)
if success:
    print("✅ Connected to Ethereum")
```

### Example 12: Connect to Ethereum Sepolia Testnet
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
print("✅ Connected to Sepolia")
```

### Example 13: Connect to Polygon Mainnet
```python
manager = BlockchainManager()
manager.connect(ChainType.POLYGON)
print("✅ Connected to Polygon")
```

### Example 14: Connect to Polygon Amoy Testnet
```python
manager = BlockchainManager()
manager.connect(ChainType.POLYGON_AMOY)
print("✅ Connected to Amoy")
```

### Example 15: Switch Between Chains
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
print("Connected to Sepolia")

manager.switch_chain(ChainType.POLYGON_AMOY)
print("Switched to Amoy")
```

### Example 16: Disconnect from Current Chain
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
manager.disconnect()
print("Disconnected")
```

### Example 17: Connect with Error Handling
```python
manager = BlockchainManager()
try:
    success = manager.connect(ChainType.ETHEREUM_SEPOLIA)
    if success:
        print("✅ Connected successfully")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### Example 18: Connect to Multiple Chains in Sequence
```python
manager = BlockchainManager()
chains = [ChainType.ETHEREUM_SEPOLIA, ChainType.POLYGON_AMOY]
for chain in chains:
    manager.connect(chain)
    print(f"Connected to {chain.value}")
```

### Example 19: Get Current Active Chain
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
active = manager.active_chain
print(f"Active chain: {active.value}")
```

### Example 20: Reconnect to Same Chain
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
manager.disconnect()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
print("Reconnected")
```

---

## Section 3: Balance Queries (21-30)

### Example 21: Get ETH Balance
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
balance = manager.get_balance(address)
print(f"Balance: {balance} ETH")
```

### Example 22: Get Balance with Error Handling
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
try:
    balance = manager.get_balance("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
    print(f"Balance: {balance:.6f} ETH")
except Exception as e:
    print(f"Error: {e}")
```

### Example 23: Get Balance on Specific Chain
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
balance = manager.get_balance(
    "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    chain=ChainType.ETHEREUM_SEPOLIA
)
print(f"Sepolia Balance: {balance} ETH")
```

### Example 24: Check Multiple Wallet Balances
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
wallets = [
    "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEc"
]
for wallet in wallets:
    try:
        balance = manager.get_balance(wallet)
        print(f"{wallet[:10]}...{wallet[-8:]}: {balance:.6f} ETH")
    except:
        print(f"{wallet}: Error fetching balance")
```

### Example 25: Get MATIC Balance on Polygon
```python
manager = BlockchainManager()
manager.connect(ChainType.POLYGON_AMOY)
balance = manager.get_balance("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
print(f"Balance: {balance} MATIC")
```

### Example 26: Format Balance for Display
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
balance = manager.get_balance("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
formatted = f"{balance:.4f} ETH"
print(f"Formatted: {formatted}")
```

### Example 27: Check if Wallet Has Sufficient Balance
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
balance = manager.get_balance("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
required = 0.01
if balance >= required:
    print("✅ Sufficient balance")
else:
    print(f"❌ Need {required - balance:.6f} more ETH")
```

### Example 28: Get Balance in Wei
```python
from web3 import Web3

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
balance_eth = manager.get_balance("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
balance_wei = Web3.to_wei(balance_eth, 'ether')
print(f"Balance: {balance_wei} wei")
```

### Example 29: Monitor Balance Changes
```python
import time

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

prev_balance = manager.get_balance(address)
time.sleep(10)
new_balance = manager.get_balance(address)

if new_balance != prev_balance:
    print(f"Balance changed: {new_balance - prev_balance:.6f} ETH")
```

### Example 30: Get Balance with Retry Logic
```python
import time

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

def get_balance_with_retry(address, max_retries=3):
    for i in range(max_retries):
        try:
            return manager.get_balance(address)
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2)
    
balance = get_balance_with_retry("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
print(f"Balance: {balance} ETH")
```

---

## Section 4: Gas Estimation (31-40)

### Example 31: Estimate Transfer Cost
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
estimate = manager.estimate_transaction_cost(
    "transfer",
    from_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    to_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEc",
    amount=0.01
)
print(f"Estimated gas: {estimate.estimated_gas}")
print(f"Gas price: {estimate.recommended_gas_price} Gwei")
print(f"Total cost: {estimate.total_cost_native:.6f} ETH")
```

### Example 32: Estimate ERC20 Transfer Cost
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
estimate = manager.estimate_transaction_cost(
    "erc20_transfer",
    contract_address="0xTokenContract",
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=1000000
)
print(f"ERC20 transfer will cost: {estimate.total_cost_native:.6f} ETH")
```

### Example 33: Estimate NFT Mint Cost
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
estimate = manager.estimate_transaction_cost(
    "erc721_mint",
    contract_address="0xNFTContract",
    to_address="0xRecipient",
    token_id=1
)
print(f"NFT mint cost: ${estimate.total_cost_usd:.2f} USD")
```

### Example 34: Compare Gas Prices (Slow, Standard, Fast)
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
estimate = manager.estimate_transaction_cost("transfer")
print(f"Current: {estimate.current_gas_price:.2f} Gwei")
print(f"Recommended: {estimate.recommended_gas_price:.2f} Gwei")
print(f"Fast: {estimate.fast_gas_price:.2f} Gwei")
```

### Example 35: Check if Estimate Exceeds Limits
```python
manager = BlockchainManager()
limits = TransactionLimits(max_total_cost=0.001)
manager.set_transaction_limits(limits)
manager.connect(ChainType.ETHEREUM_SEPOLIA)

estimate = manager.estimate_transaction_cost("transfer", amount=0.01)
if estimate.will_exceed_limits:
    print("⚠️ Transaction exceeds limits!")
    for limit in estimate.exceeded_limits:
        print(f"  - {limit}")
```

### Example 36: Estimate Contract Deployment Cost
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
estimate = manager.estimate_transaction_cost("contract_deploy")
print(f"Deployment cost: {estimate.total_cost_native:.6f} ETH")
print(f"Gas needed: {estimate.estimated_gas:,} units")
```

### Example 37: Compare Costs Across Chains
```python
manager = BlockchainManager()
chains = [ChainType.ETHEREUM_SEPOLIA, ChainType.POLYGON_AMOY]

for chain in chains:
    manager.connect(chain)
    estimate = manager.estimate_transaction_cost("erc721_mint")
    print(f"{chain.value}: ${estimate.total_cost_usd:.2f}")
```

### Example 38: Estimate with Current Gas Price
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
estimate = manager.estimate_transaction_cost("transfer")
total_gas_cost_gwei = estimate.estimated_gas * estimate.current_gas_price / 1e9
print(f"Gas cost: {total_gas_cost_gwei:.6f} ETH")
```

### Example 39: Calculate Max Transaction Cost
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
estimate = manager.estimate_transaction_cost("transfer")
max_cost = estimate.estimated_gas * estimate.fast_gas_price / 1e9
print(f"Max possible cost (fast): {max_cost:.6f} ETH")
```

### Example 40: Estimate Multiple Transaction Types
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_types = ["transfer", "erc20_transfer", "erc721_mint"]
for tx_type in tx_types:
    estimate = manager.estimate_transaction_cost(tx_type)
    print(f"{tx_type}: {estimate.total_cost_native:.6f} ETH")
```

---

## Section 5: Native Token Transactions (41-50)

### Example 41: Send ETH Transaction
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx = manager.send_transaction(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=0.001,
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)
print(f"Transaction: {tx.tx_hash}")
```

### Example 42: Send Transaction with Force Override
```python
import os

manager = BlockchainManager()
limits = TransactionLimits(max_total_cost=0.0001)
manager.set_transaction_limits(limits)
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx = manager.send_transaction(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=0.001,
    private_key=os.getenv("WALLET_PRIVATE_KEY"),
    force=True  # Override limits
)
```

### Example 43: Send Transaction Without Auto-Estimation
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx = manager.send_transaction(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=0.001,
    private_key=os.getenv("WALLET_PRIVATE_KEY"),
    auto_estimate=False  # Skip estimation
)
```

### Example 44: Send MATIC on Polygon
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.POLYGON_AMOY)

tx = manager.send_transaction(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=0.01,  # 0.01 MATIC
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)
```

### Example 45: Send Transaction with Error Handling
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

try:
    tx = manager.send_transaction(
        from_address="0xYourAddress",
        to_address="0xRecipient",
        amount=0.001,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
    print(f"✅ Success: {tx.tx_hash}")
except ValueError as e:
    print(f"❌ Validation error: {e}")
except Exception as e:
    print(f"❌ Transaction failed: {e}")
```

### Example 46: Wait for Transaction Confirmation
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx = manager.send_transaction(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=0.001,
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)

print("Waiting for confirmation...")
receipt = manager.wait_for_transaction_receipt(tx.tx_hash, timeout=120)
print(f"Status: {receipt['status']}")
print(f"Block: {receipt['blockNumber']}")
print(f"Gas used: {receipt['gasUsed']}")
```

### Example 47: Send Multiple Transactions in Sequence
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)
recipients = ["0xRecipient1", "0xRecipient2", "0xRecipient3"]

for recipient in recipients:
    tx = manager.send_transaction(
        from_address="0xYourAddress",
        to_address=recipient,
        amount=0.001,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
    print(f"Sent to {recipient}: {tx.tx_hash}")
```

### Example 48: Get Transaction Details After Sending
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx = manager.send_transaction(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=0.001,
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)

# Wait for confirmation
receipt = manager.wait_for_transaction_receipt(tx.tx_hash)

# Get full details
details = manager.get_transaction(tx.tx_hash)
print(f"From: {details['from']}")
print(f"To: {details['to']}")
print(f"Value: {details['value']} ETH")
print(f"Gas used: {details['gas_used']}")
```

### Example 49: Send Transaction with Specific Chain
```python
import os

manager = BlockchainManager()

tx = manager.send_transaction(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=0.001,
    private_key=os.getenv("WALLET_PRIVATE_KEY"),
    chain=ChainType.ETHEREUM_SEPOLIA
)
```

### Example 50: Batch Send to Multiple Recipients
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

recipients = {
    "0xRecipient1": 0.001,
    "0xRecipient2": 0.002,
    "0xRecipient3": 0.003
}

for recipient, amount in recipients.items():
    try:
        tx = manager.send_transaction(
            from_address="0xYourAddress",
            to_address=recipient,
            amount=amount,
            private_key=os.getenv("WALLET_PRIVATE_KEY")
        )
        print(f"✅ {recipient}: {tx.tx_hash}")
    except Exception as e:
        print(f"❌ {recipient}: {e}")
```

---

## Section 6: ERC20 Token Operations (51-60)

### Example 51: Transfer ERC20 Tokens
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_hash = manager.transfer_erc20(
    contract_address="0xTokenContract",
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=1000000000000000000,  # 1 token (18 decimals)
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)
print(f"ERC20 transfer: {tx_hash}")
```

### Example 52: Get ERC20 Balance
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

balance = manager.get_erc20_balance(
    contract_address="0xTokenContract",
    wallet_address="0xYourAddress"
)
print(f"Token balance: {balance}")
```

### Example 53: Convert ERC20 Balance to Human-Readable
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

balance = manager.get_erc20_balance(
    contract_address="0xTokenContract",
    wallet_address="0xYourAddress"
)
decimals = 18
readable = balance / (10 ** decimals)
print(f"Balance: {readable} tokens")
```

### Example 54: Transfer USDC (6 Decimals)
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

# Transfer 100 USDC (6 decimals)
tx_hash = manager.transfer_erc20(
    contract_address="0xUSDCContract",
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=100000000,  # 100 USDC
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)
```

### Example 55: Check ERC20 Balance Before Transfer
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

balance = manager.get_erc20_balance(
    contract_address="0xTokenContract",
    wallet_address="0xYourAddress"
)

amount_to_send = 1000000000000000000
if balance >= amount_to_send:
    tx_hash = manager.transfer_erc20(
        contract_address="0xTokenContract",
        from_address="0xYourAddress",
        to_address="0xRecipient",
        amount=amount_to_send,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
    print("✅ Transfer successful")
else:
    print("❌ Insufficient balance")
```

### Example 56: Transfer ERC20 with Force Override
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_hash = manager.transfer_erc20(
    contract_address="0xTokenContract",
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=1000000000000000000,
    private_key=os.getenv("WALLET_PRIVATE_KEY"),
    force=True
)
```

### Example 57: Transfer ERC20 Without Auto-Estimation
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_hash = manager.transfer_erc20(
    contract_address="0xTokenContract",
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=1000000000000000000,
    private_key=os.getenv("WALLET_PRIVATE_KEY"),
    auto_estimate=False
)
```

### Example 58: Batch Transfer ERC20 to Multiple Recipients
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

recipients = {
    "0xRecipient1": 1000000000000000000,
    "0xRecipient2": 2000000000000000000,
    "0xRecipient3": 3000000000000000000
}

for recipient, amount in recipients.items():
    tx_hash = manager.transfer_erc20(
        contract_address="0xTokenContract",
        from_address="0xYourAddress",
        to_address=recipient,
        amount=amount,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
    print(f"Sent to {recipient}: {tx_hash}")
```

### Example 59: Monitor ERC20 Balance Changes
```python
import time

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

prev_balance = manager.get_erc20_balance(
    contract_address="0xTokenContract",
    wallet_address="0xYourAddress"
)

time.sleep(30)

new_balance = manager.get_erc20_balance(
    contract_address="0xTokenContract",
    wallet_address="0xYourAddress"
)

if new_balance != prev_balance:
    diff = new_balance - prev_balance
    print(f"Balance changed: {diff} tokens")
```

### Example 60: Transfer ERC20 on Polygon
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.POLYGON_AMOY)

tx_hash = manager.transfer_erc20(
    contract_address="0xPolygonTokenContract",
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=1000000000000000000,
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)
print(f"Polygon ERC20 transfer: {tx_hash}")
```

---

## Section 7: ERC721 NFT Operations (61-70)

### Example 61: Mint NFT
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_hash = manager.mint_erc721(
    contract_address="0xNFTContract",
    to_address="0xRecipient",
    token_id=1,
    private_key=os.getenv("WALLET_PRIVATE_KEY"),
    metadata_uri="ipfs://QmYourMetadataHash"
)
print(f"NFT minted: {tx_hash}")
```

### Example 62: Mint NFT Without Auto-Estimation
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_hash = manager.mint_erc721(
    contract_address="0xNFTContract",
    to_address="0xRecipient",
    token_id=1,
    private_key=os.getenv("WALLET_PRIVATE_KEY"),
    auto_estimate=False
)
```

### Example 63: Mint NFT with Force Override
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_hash = manager.mint_erc721(
    contract_address="0xNFTContract",
    to_address="0xRecipient",
    token_id=1,
    private_key=os.getenv("WALLET_PRIVATE_KEY"),
    force=True
)
```

### Example 64: Get NFT Owner
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

owner = manager.get_erc721_owner(
    contract_address="0xNFTContract",
    token_id=1
)
print(f"NFT owner: {owner}")
```

### Example 65: Transfer NFT
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_hash = manager.transfer_erc721(
    contract_address="0xNFTContract",
    from_address="0xYourAddress",
    to_address="0xRecipient",
    token_id=1,
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)
print(f"NFT transferred: {tx_hash}")
```

### Example 66: Verify NFT Ownership Before Transfer
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

owner = manager.get_erc721_owner(
    contract_address="0xNFTContract",
    token_id=1
)

if owner.lower() == "0xYourAddress".lower():
    tx_hash = manager.transfer_erc721(
        contract_address="0xNFTContract",
        from_address="0xYourAddress",
        to_address="0xRecipient",
        token_id=1,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
    print("✅ Transfer successful")
else:
    print("❌ You don't own this NFT")
```

### Example 67: Mint Multiple NFTs in Sequence
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

for token_id in range(1, 6):
    tx_hash = manager.mint_erc721(
        contract_address="0xNFTContract",
        to_address="0xRecipient",
        token_id=token_id,
        private_key=os.getenv("WALLET_PRIVATE_KEY"),
        metadata_uri=f"ipfs://QmHash{token_id}"
    )
    print(f"Minted NFT #{token_id}: {tx_hash}")
```

### Example 68: Mint NFT with Wait for Confirmation
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_hash = manager.mint_erc721(
    contract_address="0xNFTContract",
    to_address="0xRecipient",
    token_id=1,
    private_key=os.getenv("WALLET_PRIVATE_KEY"),
    metadata_uri="ipfs://QmHash"
)

print("Waiting for confirmation...")
receipt = manager.wait_for_transaction_receipt(tx_hash)

if receipt['status'] == 'success':
    print("✅ NFT minted successfully!")
    owner = manager.get_erc721_owner("0xNFTContract", 1)
    print(f"Owner: {owner}")
```

### Example 69: Mint NFT on Polygon
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.POLYGON_AMOY)

tx_hash = manager.mint_erc721(
    contract_address="0xPolygonNFTContract",
    to_address="0xRecipient",
    token_id=1,
    private_key=os.getenv("WALLET_PRIVATE_KEY"),
    metadata_uri="ipfs://QmHash"
)
print(f"NFT minted on Polygon: {tx_hash}")
```

### Example 70: Batch Mint NFTs to Multiple Recipients
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

recipients = ["0xRecipient1", "0xRecipient2", "0xRecipient3"]

for i, recipient in enumerate(recipients, start=1):
    tx_hash = manager.mint_erc721(
        contract_address="0xNFTContract",
        to_address=recipient,
        token_id=i,
        private_key=os.getenv("WALLET_PRIVATE_KEY"),
        metadata_uri=f"ipfs://QmHash{i}"
    )
    print(f"Minted NFT #{i} to {recipient}: {tx_hash}")
```

---

## Section 8: Smart Contract Operations (71-75)

### Example 71: Deploy Smart Contract
```python
import os
import json

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

# Load ABI and bytecode
with open('contract_abi.json') as f:
    abi = json.load(f)

with open('contract_bytecode.txt') as f:
    bytecode = f.read()

contract = manager.deploy_contract(
    abi=abi,
    bytecode=bytecode,
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)

print(f"Contract deployed at: {contract.address}")
```

### Example 72: Deploy Contract and Wait for Confirmation
```python
import os
import json

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

with open('contract_abi.json') as f:
    abi = json.load(f)

with open('contract_bytecode.txt') as f:
    bytecode = f.read()

contract = manager.deploy_contract(
    abi=abi,
    bytecode=bytecode,
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)

print(f"✅ Contract deployed at: {contract.address}")
print(f"   Deployed at: {contract.deployed_at}")
print(f"   Chain: {contract.chain.value}")
```

### Example 73: Deploy Multiple Contracts
```python
import os
import json

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

contracts = []
for i in range(3):
    with open(f'contract_{i}_abi.json') as f:
        abi = json.load(f)
    
    with open(f'contract_{i}_bytecode.txt') as f:
        bytecode = f.read()
    
    contract = manager.deploy_contract(
        abi=abi,
        bytecode=bytecode,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
    contracts.append(contract)
    print(f"Contract {i} deployed at: {contract.address}")
```

### Example 74: Estimate Contract Deployment Cost
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

estimate = manager.estimate_transaction_cost("contract_deploy")
print(f"Deployment will cost approximately:")
print(f"  Gas: {estimate.estimated_gas:,} units")
print(f"  Cost: {estimate.total_cost_native:.6f} ETH")
print(f"  USD: ${estimate.total_cost_usd:.2f}")
```

### Example 75: Deploy Contract on Different Chains
```python
import os
import json

manager = BlockchainManager()

chains = [ChainType.ETHEREUM_SEPOLIA, ChainType.POLYGON_AMOY]

with open('contract_abi.json') as f:
    abi = json.load(f)

with open('contract_bytecode.txt') as f:
    bytecode = f.read()

for chain in chains:
    manager.connect(chain)
    contract = manager.deploy_contract(
        abi=abi,
        bytecode=bytecode,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
    print(f"{chain.value}: {contract.address}")
```

---

## Section 9: Transaction History & Monitoring (76-85)

### Example 76: Get Transaction History
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

# After sending some transactions
history = manager.get_transaction_history()
print(f"Total transactions: {len(history)}")
for tx in history:
    print(f"  {tx.tx_hash}: {tx.amount} {tx.chain.value}")
```

### Example 77: Get Transaction History for Specific Chain
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

# After sending transactions on multiple chains
history = manager.get_transaction_history(chain=ChainType.ETHEREUM_SEPOLIA)
print(f"Sepolia transactions: {len(history)}")
```

### Example 78: Filter Transaction History by Status
```python
manager = BlockchainManager()
history = manager.get_transaction_history()

pending = [tx for tx in history if tx.status == "pending"]
completed = [tx for tx in history if tx.status == "sent"]

print(f"Pending: {len(pending)}")
print(f"Completed: {len(completed)}")
```

### Example 79: Get Transaction Details by Hash
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_hash = "0x1234..."
details = manager.get_transaction(tx_hash)

print(f"From: {details['from']}")
print(f"To: {details['to']}")
print(f"Value: {details['value']} ETH")
print(f"Status: {details['status']}")
print(f"Block: {details['block_number']}")
```

### Example 80: Monitor Transaction Status
```python
import time

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_hash = "0x1234..."

while True:
    try:
        details = manager.get_transaction(tx_hash)
        print(f"Status: {details['status']}")
        if details['status'] == 'success':
            print("✅ Transaction confirmed!")
            break
    except:
        print("Transaction pending...")
    
    time.sleep(10)
```

### Example 81: Calculate Total Gas Spent
```python
manager = BlockchainManager()
history = manager.get_transaction_history()

total_gas = 0
for tx in history:
    if tx.gas_fee:
        total_gas += tx.gas_fee

print(f"Total gas spent: {total_gas} ETH")
```

### Example 82: Export Transaction History to CSV
```python
import csv

manager = BlockchainManager()
history = manager.get_transaction_history()

with open('transaction_history.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Hash', 'From', 'To', 'Amount', 'Chain', 'Status'])
    
    for tx in history:
        writer.writerow([
            tx.tx_hash,
            tx.from_address,
            tx.to_address,
            tx.amount,
            tx.chain.value,
            tx.status
        ])

print("✅ Exported to transaction_history.csv")
```

### Example 83: Get Recent Transactions
```python
manager = BlockchainManager()
history = manager.get_transaction_history()

# Get last 5 transactions
recent = history[-5:]
for tx in recent:
    print(f"{tx.tx_hash}: {tx.amount} ETH")
```

### Example 84: Filter Transactions by Amount
```python
manager = BlockchainManager()
history = manager.get_transaction_history()

large_txs = [tx for tx in history if tx.amount > 0.01]
print(f"Large transactions (>0.01 ETH): {len(large_txs)}")
```

### Example 85: Get Failed Transactions
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

history = manager.get_transaction_history()

for tx in history:
    try:
        details = manager.get_transaction(tx.tx_hash)
        if details['status'] == 'failed':
            print(f"❌ Failed: {tx.tx_hash}")
    except:
        pass
```

---

## Section 10: Advanced Features & Best Practices (86-100)

### Example 86: Retry Failed Transactions
```python
import os
import time

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

def send_with_retry(from_addr, to_addr, amount, max_retries=3):
    for i in range(max_retries):
        try:
            tx = manager.send_transaction(
                from_address=from_addr,
                to_address=to_addr,
                amount=amount,
                private_key=os.getenv("WALLET_PRIVATE_KEY")
            )
            return tx
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            if i < max_retries - 1:
                time.sleep(5)
    raise Exception("All retries failed")

tx = send_with_retry("0xYourAddress", "0xRecipient", 0.001)
print(f"Success: {tx.tx_hash}")
```

### Example 87: Implement Rate Limiting
```python
import os
import time

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

recipients = ["0xRecipient1", "0xRecipient2", "0xRecipient3"]
delay = 5  # seconds between transactions

for recipient in recipients:
    tx = manager.send_transaction(
        from_address="0xYourAddress",
        to_address=recipient,
        amount=0.001,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
    print(f"Sent to {recipient}: {tx.tx_hash}")
    time.sleep(delay)
```

### Example 88: Validate Address Before Transaction
```python
import os
from web3 import Web3

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

recipient = "0xRecipient"

if Web3.is_address(recipient):
    tx = manager.send_transaction(
        from_address="0xYourAddress",
        to_address=recipient,
        amount=0.001,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
    print("✅ Transaction sent")
else:
    print("❌ Invalid address")
```

### Example 89: Check Network Before Sending
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

if manager.is_testnet():
    print("✅ Safe - sending on testnet")
    tx = manager.send_transaction(
        from_address="0xYourAddress",
        to_address="0xRecipient",
        amount=0.001,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
else:
    print("⚠️  Warning - mainnet transaction!")
```

### Example 90: Log All Transactions to File
```python
import os
import logging

# Configure logging
logging.basicConfig(
    filename='transactions.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx = manager.send_transaction(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=0.001,
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)

logging.info(f"TX: {tx.tx_hash} | Amount: {tx.amount} | Status: {tx.status}")
```

### Example 91: Implement Transaction Queue
```python
import os
from queue import Queue

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx_queue = Queue()

# Add transactions to queue
tx_queue.put(("0xRecipient1", 0.001))
tx_queue.put(("0xRecipient2", 0.002))
tx_queue.put(("0xRecipient3", 0.003))

# Process queue
while not tx_queue.empty():
    recipient, amount = tx_queue.get()
    try:
        tx = manager.send_transaction(
            from_address="0xYourAddress",
            to_address=recipient,
            amount=amount,
            private_key=os.getenv("WALLET_PRIVATE_KEY")
        )
        print(f"✅ Sent to {recipient}: {tx.tx_hash}")
    except Exception as e:
        print(f"❌ Failed {recipient}: {e}")
```

### Example 92: Calculate Transaction Costs in Different Currencies
```python
manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

estimate = manager.estimate_transaction_cost("transfer")

# Get ETH price (example: $3000)
eth_price = 3000

cost_eth = estimate.total_cost_native
cost_usd = cost_eth * eth_price
cost_eur = cost_usd * 0.92  # Example exchange rate

print(f"Cost: {cost_eth:.6f} ETH")
print(f"Cost: ${cost_usd:.2f} USD")
print(f"Cost: €{cost_eur:.2f} EUR")
```

### Example 93: Implement Multi-Signature Workflow
```python
import os

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

# Estimate first
estimate = manager.estimate_transaction_cost(
    "transfer",
    from_address="0xMultisigAddress",
    to_address="0xRecipient",
    amount=1.0
)

print(f"Transaction requires approval")
print(f"Cost: {estimate.total_cost_native:.6f} ETH")

# In production, this would require multiple signatures
approval = input("Approve? (yes/no): ")

if approval.lower() == "yes":
    tx = manager.send_transaction(
        from_address="0xMultisigAddress",
        to_address="0xRecipient",
        amount=1.0,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
    print(f"✅ Executed: {tx.tx_hash}")
```

### Example 94: Implement Gas Price Alert System
```python
import time

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM)

threshold = 50  # Gwei

while True:
    estimate = manager.estimate_transaction_cost("transfer")
    current_gas = estimate.current_gas_price
    
    print(f"Current gas: {current_gas:.2f} Gwei")
    
    if current_gas < threshold:
        print(f"✅ Gas below {threshold} Gwei - good time to transact!")
        break
    else:
        print(f"⏳ Waiting for gas to drop below {threshold} Gwei...")
        time.sleep(60)
```

### Example 95: Batch Operations with Progress Bar
```python
import os
from tqdm import tqdm

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

recipients = ["0xRecipient1", "0xRecipient2", "0xRecipient3", "0xRecipient4"]

for recipient in tqdm(recipients, desc="Sending transactions"):
    tx = manager.send_transaction(
        from_address="0xYourAddress",
        to_address=recipient,
        amount=0.001,
        private_key=os.getenv("WALLET_PRIVATE_KEY")
    )
```

### Example 96: Implement Transaction Confirmation Checker
```python
import os
import time

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

tx = manager.send_transaction(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount=0.001,
    private_key=os.getenv("WALLET_PRIVATE_KEY")
)

print(f"Transaction sent: {tx.tx_hash}")
print("Waiting for confirmations...")

receipt = manager.wait_for_transaction_receipt(tx.tx_hash, timeout=180)

print(f"✅ Confirmed in block {receipt['blockNumber']}")
print(f"   Gas used: {receipt['gasUsed']}")
print(f"   Status: {receipt['status']}")
```

### Example 97: Compare Costs Across All Available Chains
```python
manager = BlockchainManager()

chains = manager.get_supported_chains()
costs = {}

for chain in chains:
    try:
        manager.connect(chain)
        estimate = manager.estimate_transaction_cost("erc721_mint")
        costs[chain.value] = estimate.total_cost_usd or 0
    except:
        costs[chain.value] = None

print("NFT Minting Costs:")
for chain, cost in sorted(costs.items(), key=lambda x: x[1] or float('inf')):
    if cost is not None:
        print(f"  {chain}: ${cost:.2f}")
    else:
        print(f"  {chain}: N/A")
```

### Example 98: Implement Automatic Fallback to Alternative RPC
```python
import os

manager = BlockchainManager()

rpc_urls = [
    "https://rpc.sepolia.org",
    "https://ethereum-sepolia.publicnode.com",
    "https://rpc2.sepolia.org"
]

connected = False
for rpc_url in rpc_urls:
    try:
        os.environ["SEPOLIA_RPC_URL"] = rpc_url
        manager = BlockchainManager()
        if manager.connect(ChainType.ETHEREUM_SEPOLIA):
            print(f"✅ Connected via {rpc_url}")
            connected = True
            break
    except:
        print(f"❌ Failed: {rpc_url}")

if not connected:
    print("❌ All RPC endpoints failed")
```

### Example 99: Create Transaction Dashboard
```python
import os
from datetime import datetime

manager = BlockchainManager()
manager.connect(ChainType.ETHEREUM_SEPOLIA)

def print_dashboard():
    print("\n" + "="*60)
    print("BLOCKCHAIN MANAGER DASHBOARD")
    print("="*60)
    
    # Network info
    config = manager.get_network_config()
    print(f"\n📡 Network: {config.native_currency} ({config.chain_id})")
    print(f"   Type: {'Testnet' if config.is_testnet else 'Mainnet'}")
    
    # Gas prices
    estimate = manager.estimate_transaction_cost("transfer")
    print(f"\n⛽ Gas Prices:")
    print(f"   Current: {estimate.current_gas_price:.2f} Gwei")
    print(f"   Fast: {estimate.fast_gas_price:.2f} Gwei")
    
    # Transaction history
    history = manager.get_transaction_history()
    print(f"\n📊 Transaction History:")
    print(f"   Total: {len(history)}")
    
    # Balance check
    try:
        balance = manager.get_balance("0xYourAddress")
        print(f"\n💰 Balance: {balance:.6f} {config.native_currency}")
    except:
        print(f"\n💰 Balance: N/A")
    
    # Limits
    limits = manager.get_transaction_limits()
    print(f"\n🔒 Transaction Limits:")
    print(f"   Max gas price: {limits.max_gas_price} Gwei")
    print(f"   Max cost: {limits.max_total_cost}")
    
    print("\n" + "="*60 + "\n")

print_dashboard()
```

### Example 100: Complete Production Workflow
```python
import os
import time
import logging
from web3 import Web3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('blockchain.log'),
        logging.StreamHandler()
    ]
)

def production_workflow():
    """Complete production workflow with all best practices"""
    
    # 1. Initialize manager
    manager = BlockchainManager()
    logging.info("Manager initialized")
    
    # 2. Set transaction limits
    limits = TransactionLimits(
        max_gas_price=100.0,
        max_total_cost=0.05,
        max_gas_limit=500000
    )
    manager.set_transaction_limits(limits)
    logging.info("Transaction limits set")
    
    # 3. Connect to network
    try:
        success = manager.connect(ChainType.ETHEREUM_SEPOLIA)
        if not success:
            raise Exception("Connection failed")
        logging.info("Connected to Sepolia testnet")
    except Exception as e:
        logging.error(f"Connection error: {e}")
        return
    
    # 4. Verify network
    if not manager.is_testnet():
        logging.warning("⚠️  MAINNET DETECTED - Proceed with caution")
        confirm = input("Continue on mainnet? (yes/no): ")
        if confirm.lower() != "yes":
            return
    
    # 5. Validate addresses
    from_address = "0xYourAddress"
    to_address = "0xRecipient"
    
    if not Web3.is_address(from_address) or not Web3.is_address(to_address):
        logging.error("Invalid address detected")
        return
    
    # 6. Check balance
    try:
        balance = manager.get_balance(from_address)
        logging.info(f"Balance: {balance:.6f} ETH")
        
        if balance < 0.01:
            logging.error("Insufficient balance")
            return
    except Exception as e:
        logging.error(f"Balance check failed: {e}")
        return
    
    # 7. Estimate transaction cost
    try:
        estimate = manager.estimate_transaction_cost(
            "transfer",
            from_address=from_address,
            to_address=to_address,
            amount=0.001
        )
        
        logging.info(f"Estimated cost: {estimate.total_cost_native:.6f} ETH")
        logging.info(f"Gas price: {estimate.recommended_gas_price:.2f} Gwei")
        
        if estimate.will_exceed_limits:
            logging.warning("Transaction exceeds limits")
            for limit in estimate.exceeded_limits:
                logging.warning(f"  - {limit}")
            return
    except Exception as e:
        logging.error(f"Estimation failed: {e}")
        return
    
    # 8. Send transaction
    try:
        tx = manager.send_transaction(
            from_address=from_address,
            to_address=to_address,
            amount=0.001,
            private_key=os.getenv("WALLET_PRIVATE_KEY"),
            auto_estimate=True,
            force=False
        )
        
        logging.info(f"✅ Transaction sent: {tx.tx_hash}")
        
        # 9. Wait for confirmation
        logging.info("Waiting for confirmation...")
        receipt = manager.wait_for_transaction_receipt(tx.tx_hash, timeout=180)
        
        if receipt['status'] == 'success':
            logging.info(f"✅ Transaction confirmed in block {receipt['blockNumber']}")
            logging.info(f"   Gas used: {receipt['gasUsed']}")
        else:
            logging.error("❌ Transaction failed")
            
    except ValueError as e:
        logging.error(f"Validation error: {e}")
    except Exception as e:
        logging.error(f"Transaction failed: {e}")
    
    # 10. Log final state
    history = manager.get_transaction_history()
    logging.info(f"Total transactions: {len(history)}")
    
    final_balance = manager.get_balance(from_address)
    logging.info(f"Final balance: {final_balance:.6f} ETH")

# Run the workflow
if __name__ == "__main__":
    production_workflow()
```

---

## Summary

This document provides 100 comprehensive examples covering:

1. **Initialization & Configuration** (1-10)
2. **Network Connections** (11-20)
3. **Balance Queries** (21-30)
4. **Gas Estimation** (31-40)
5. **Native Token Transactions** (41-50)
6. **ERC20 Token Operations** (51-60)
7. **ERC721 NFT Operations** (61-70)
8. **Smart Contract Operations** (71-75)
9. **Transaction History & Monitoring** (76-85)
10. **Advanced Features & Best Practices** (86-100)

## Additional Resources

- **Documentation**: See code docstrings for detailed API reference
- **Security**: Review Example 100 for production best practices
- **Testing**: Always test on testnets before mainnet deployment
- **Support**: Check logs for debugging information

## Environment Setup Reminder

```bash
# .env file
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
SEPOLIA_RPC_URL=https://rpc.sepolia.org
POLYGON_RPC_URL=https://polygon-rpc.com
AMOY_RPC_URL=https://rpc-amoy.polygon.technology
WALLET_PRIVATE_KEY=your_private_key_here
COINGECKO_API_KEY=your_api_key (optional)
```

**⚠️ NEVER commit your `.env` file or expose private keys!**