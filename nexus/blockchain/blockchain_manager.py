"""
Production-Ready Multi-Chain Blockchain Manager

Installation:
    pip install web3>=6.0.0 eth-account python-dotenv requests

Environment variables (.env):
    ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
    SEPOLIA_RPC_URL=https://rpc.sepolia.org
    HOLESKY_RPC_URL=https://ethereum-holesky.publicnode.com
    POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_API_KEY
    AMOY_RPC_URL=https://rpc-amoy.polygon.technology
    COINGECKO_API_KEY=your_coingecko_api_key (optional)
    WALLET_PRIVATE_KEY=your_private_key (NEVER commit this!)

Author: AI Assistant
License: MIT
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import logging
from decimal import Decimal
import os
from dotenv import load_dotenv

# Web3 and blockchain imports
try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
    from eth_account import Account
    from eth_account.signers.local import LocalAccount
except ImportError:
    raise ImportError(
        "Missing dependencies. Install with: "
        "pip install web3>=6.0.0 eth-account"
    )

try:
    import requests
except ImportError:
    raise ImportError("Install requests: pip install requests")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class ChainType(Enum):
    """Supported blockchain types"""
    # Mainnets
    ETHEREUM = "ethereum"
    BITCOIN = "bitcoin"
    SOLANA = "solana"
    POLYGON = "polygon"
    # Testnets
    ETHEREUM_SEPOLIA = "ethereum_sepolia"
    ETHEREUM_GOERLI = "ethereum_goerli"
    ETHEREUM_HOLESKY = "ethereum_holesky"
    POLYGON_MUMBAI = "polygon_mumbai"
    POLYGON_AMOY = "polygon_amoy"
    BITCOIN_TESTNET = "bitcoin_testnet"
    SOLANA_DEVNET = "solana_devnet"
    SOLANA_TESTNET = "solana_testnet"


class TokenStandard(Enum):
    """Supported token standards"""
    ERC20 = "erc20"
    ERC721 = "erc721"
    ERC1155 = "erc1155"
    SPL = "spl"  # Solana token standard


@dataclass
class NetworkConfig:
    """Network configuration for different chains"""
    chain_id: int
    rpc_url: str
    explorer_url: str
    native_currency: str
    is_testnet: bool
    faucet_url: Optional[str] = None
    gas_oracle_url: Optional[str] = None


@dataclass
class TransactionLimits:
    """User-defined transaction limits"""
    max_gas_price: Optional[float] = None  # Max gas price in Gwei
    max_gas_limit: Optional[int] = None  # Max gas units
    max_total_cost: Optional[float] = None  # Max cost in native currency
    max_priority_fee: Optional[float] = None  # Max priority fee (EIP-1559)
    slippage_tolerance: float = 0.01  # 1% default slippage
    deadline_minutes: int = 20  # Transaction deadline


@dataclass
class GasEstimate:
    """Gas estimation for a transaction"""
    estimated_gas: int
    current_gas_price: float  # In Gwei
    recommended_gas_price: float  # In Gwei
    fast_gas_price: float  # In Gwei
    total_cost_native: float  # Total cost in native currency
    total_cost_usd: Optional[float] = None
    will_exceed_limits: bool = False
    exceeded_limits: List[str] = field(default_factory=list)


@dataclass
class Transaction:
    """Transaction data structure"""
    from_address: str
    to_address: str
    amount: float
    chain: ChainType
    tx_hash: Optional[str] = None
    timestamp: Optional[float] = None
    status: str = "pending"
    gas_fee: Optional[float] = None
    token_standard: Optional[TokenStandard] = None
    token_id: Optional[int] = None
    contract_address: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None


@dataclass
class SmartContract:
    """Smart contract data structure"""
    address: str
    abi: List[Dict]
    chain: ChainType
    bytecode: Optional[str] = None
    deployed_at: Optional[float] = None


# ============================================================================
# NETWORK CONFIGURATIONS
# ============================================================================

NETWORK_CONFIGS = {
    # Ethereum Mainnet & Testnets
    ChainType.ETHEREUM: NetworkConfig(
        chain_id=1,
        rpc_url=os.getenv("ETHEREUM_RPC_URL", "https://eth.llamarpc.com"),
        explorer_url="https://etherscan.io",
        native_currency="ETH",
        is_testnet=False,
        gas_oracle_url="https://api.etherscan.io/api?module=gastracker&action=gasoracle"
    ),
    ChainType.ETHEREUM_SEPOLIA: NetworkConfig(
        chain_id=11155111,
        rpc_url=os.getenv("SEPOLIA_RPC_URL", "https://rpc.sepolia.org"),
        explorer_url="https://sepolia.etherscan.io",
        native_currency="SepoliaETH",
        is_testnet=True,
        faucet_url="https://sepoliafaucet.com"
    ),
    ChainType.ETHEREUM_HOLESKY: NetworkConfig(
        chain_id=17000,
        rpc_url=os.getenv("HOLESKY_RPC_URL", "https://ethereum-holesky.publicnode.com"),
        explorer_url="https://holesky.etherscan.io",
        native_currency="HoleskyETH",
        is_testnet=True,
        faucet_url="https://holesky-faucet.pk910.de"
    ),
    
    # Polygon Mainnet & Testnets
    ChainType.POLYGON: NetworkConfig(
        chain_id=137,
        rpc_url=os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com"),
        explorer_url="https://polygonscan.com",
        native_currency="MATIC",
        is_testnet=False
    ),
    ChainType.POLYGON_AMOY: NetworkConfig(
        chain_id=80002,
        rpc_url=os.getenv("AMOY_RPC_URL", "https://rpc-amoy.polygon.technology"),
        explorer_url="https://amoy.polygonscan.com",
        native_currency="MATIC",
        is_testnet=True,
        faucet_url="https://faucet.polygon.technology"
    ),
    
    # Bitcoin Mainnet & Testnet
    ChainType.BITCOIN: NetworkConfig(
        chain_id=0,
        rpc_url=os.getenv("BITCOIN_RPC_URL", ""),
        explorer_url="https://blockstream.info",
        native_currency="BTC",
        is_testnet=False
    ),
    ChainType.BITCOIN_TESTNET: NetworkConfig(
        chain_id=0,
        rpc_url=os.getenv("BITCOIN_TESTNET_RPC_URL", ""),
        explorer_url="https://blockstream.info/testnet",
        native_currency="tBTC",
        is_testnet=True,
        faucet_url="https://testnet-faucet.mempool.co"
    ),
    
    # Solana Mainnet & Testnets
    ChainType.SOLANA: NetworkConfig(
        chain_id=0,
        rpc_url=os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"),
        explorer_url="https://explorer.solana.com",
        native_currency="SOL",
        is_testnet=False
    ),
    ChainType.SOLANA_DEVNET: NetworkConfig(
        chain_id=0,
        rpc_url=os.getenv("SOLANA_DEVNET_RPC_URL", "https://api.devnet.solana.com"),
        explorer_url="https://explorer.solana.com?cluster=devnet",
        native_currency="SOL",
        is_testnet=True,
        faucet_url="https://faucet.solana.com"
    ),
}


# ============================================================================
# PRICE ORACLE
# ============================================================================

class PriceOracle:
    """Fetch cryptocurrency prices from CoinGecko"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    COIN_IDS = {
        "ETH": "ethereum",
        "BTC": "bitcoin",
        "SOL": "solana",
        "MATIC": "matic-network"
    }
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        self.api_key = os.getenv("COINGECKO_API_KEY")
    
    def get_price(self, symbol: str) -> float:
        """Get current price in USD with caching"""
        if symbol not in self.COIN_IDS:
            logger.warning(f"Unknown symbol: {symbol}")
            return 0.0
        
        # Check cache
        cache_key = f"{symbol}_price"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_data
        
        try:
            coin_id = self.COIN_IDS[symbol]
            url = f"{self.BASE_URL}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd"
            }
            
            if self.api_key:
                params["x_cg_demo_api_key"] = self.api_key
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            price = data.get(coin_id, {}).get("usd", 0.0)
            
            # Update cache
            self.cache[cache_key] = (price, time.time())
            return price
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return 0.0


# ============================================================================
# BLOCKCHAIN ADAPTERS
# ============================================================================

class BlockchainAdapter(ABC):
    """Abstract base class for blockchain adapters"""
    
    @abstractmethod
    def connect(self, network: str) -> bool:
        """Connect to blockchain network"""
        pass
    
    @abstractmethod
    def get_balance(self, address: str) -> float:
        """Get wallet balance"""
        pass
    
    @abstractmethod
    def send_transaction(self, tx: Transaction, private_key: str) -> str:
        """Send a transaction"""
        pass
    
    @abstractmethod
    def get_transaction(self, tx_hash: str) -> Dict:
        """Get transaction details"""
        pass
    
    @abstractmethod
    def deploy_contract(self, contract: SmartContract, private_key: str) -> str:
        """Deploy a smart contract"""
        pass
    
    @abstractmethod
    def estimate_gas(self, tx_type: str, **params) -> GasEstimate:
        """Estimate gas for a transaction"""
        pass
    
    @abstractmethod
    def get_current_gas_price(self) -> Dict[str, float]:
        """Get current gas prices"""
        pass


class EthereumAdapter(BlockchainAdapter):
    """Production Ethereum/Polygon adapter using Web3.py"""
    
    # Standard ABIs
    ERC20_ABI = [
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        }
    ]
    
    ERC721_ABI = [
        {
            "inputs": [
                {"name": "to", "type": "address"},
                {"name": "tokenId", "type": "uint256"}
            ],
            "name": "mint",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "tokenId", "type": "uint256"}],
            "name": "ownerOf",
            "outputs": [{"name": "", "type": "address"}],
            "type": "function"
        },
        {
            "inputs": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "tokenId", "type": "uint256"}
            ],
            "name": "transferFrom",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]
    
    def __init__(self, chain_type: ChainType):
        self.chain_type = chain_type
        self.network_config = NETWORK_CONFIGS[chain_type]
        self.web3: Optional[Web3] = None
        self.price_oracle = PriceOracle()
        
        # Determine native currency symbol for pricing
        if "ETH" in self.network_config.native_currency.upper():
            self.price_symbol = "ETH"
        elif "MATIC" in self.network_config.native_currency.upper():
            self.price_symbol = "MATIC"
        else:
            self.price_symbol = "ETH"
    
    def connect(self, network: str = "mainnet") -> bool:
        """Connect to Ethereum/Polygon network"""
        try:
            self.web3 = Web3(Web3.HTTPProvider(
                self.network_config.rpc_url,
                request_kwargs={'timeout': 60}
            ))
            
            # Add POA middleware for Polygon
            if "polygon" in self.chain_type.value.lower():
                self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if not self.web3.is_connected():
                logger.error(f"Failed to connect to {self.chain_type.value}")
                return False
            
            logger.info(f"✅ Connected to {self.chain_type.value}")
            logger.info(f"   Chain ID: {self.web3.eth.chain_id}")
            logger.info(f"   Block number: {self.web3.eth.block_number}")
            
            if self.network_config.is_testnet:
                logger.warning("   ⚠️  TESTNET - Use for development only")
                if self.network_config.faucet_url:
                    logger.info(f"   💧 Faucet: {self.network_config.faucet_url}")
            
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def get_balance(self, address: str) -> float:
        """Get native token balance"""
        if not self.web3:
            raise RuntimeError("Not connected to network")
        
        try:
            if not Web3.is_address(address):
                raise ValueError(f"Invalid address: {address}")
            
            balance_wei = self.web3.eth.get_balance(
                Web3.to_checksum_address(address)
            )
            balance_eth = self.web3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
            
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            raise
    
    def get_current_gas_price(self) -> Dict[str, float]:
        """Get current gas prices in Gwei"""
        if not self.web3:
            raise RuntimeError("Not connected to network")
        
        try:
            # For testnets, return lower fixed prices
            if self.network_config.is_testnet:
                return {
                    "slow": 1.0,
                    "standard": 2.0,
                    "fast": 3.0,
                    "instant": 5.0
                }
            
            # Get base fee from latest block
            latest_block = self.web3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', 0)
            base_fee_gwei = float(self.web3.from_wei(base_fee, 'gwei'))
            
            # EIP-1559 gas pricing
            try:
                priority_fee = float(self.web3.from_wei(
                    self.web3.eth.max_priority_fee, 'gwei'
                ))
            except:
                priority_fee = 2.0  # Default priority fee
            
            return {
                "slow": base_fee_gwei + priority_fee * 0.9,
                "standard": base_fee_gwei + priority_fee,
                "fast": base_fee_gwei + priority_fee * 1.2,
                "instant": base_fee_gwei + priority_fee * 1.5
            }
            
        except Exception as e:
            logger.warning(f"Error getting gas price: {e}, using defaults")
            return {
                "slow": 20.0,
                "standard": 30.0,
                "fast": 45.0,
                "instant": 60.0
            }
    
    def estimate_gas(self, tx_type: str, **params) -> GasEstimate:
        """Estimate gas for transaction"""
        if not self.web3:
            raise RuntimeError("Not connected to network")
        
        # Gas estimates for different operations
        gas_estimates = {
            "transfer": 21000,
            "erc20_transfer": 65000,
            "erc20_approve": 46000,
            "erc721_mint": 150000,
            "erc721_transfer": 85000,
            "erc1155_mint": 100000,
            "erc1155_transfer": 75000,
            "contract_deploy": 1500000,
            "swap": 180000,
        }
        
        estimated_gas = gas_estimates.get(tx_type, 100000)
        
        # Try to get more accurate estimate for specific transactions
        try:
            if tx_type == "transfer" and "to_address" in params:
                estimated_gas = self.web3.eth.estimate_gas({
                    'from': params.get('from_address', 
                                      '0x0000000000000000000000000000000000000000'),
                    'to': Web3.to_checksum_address(params['to_address']),
                    'value': self.web3.to_wei(params.get('amount', 0), 'ether')
                })
        except Exception as e:
            logger.debug(f"Could not estimate gas accurately: {e}")
        
        gas_prices = self.get_current_gas_price()
        recommended_gas_price = gas_prices["standard"]
        
        # Calculate total cost
        total_cost_native = (estimated_gas * recommended_gas_price) / 1e9
        
        # Get USD price
        total_cost_usd = 0.0
        if not self.network_config.is_testnet:
            price_usd = self.price_oracle.get_price(self.price_symbol)
            total_cost_usd = total_cost_native * price_usd
        
        return GasEstimate(
            estimated_gas=estimated_gas,
            current_gas_price=gas_prices["standard"],
            recommended_gas_price=recommended_gas_price,
            fast_gas_price=gas_prices["fast"],
            total_cost_native=total_cost_native,
            total_cost_usd=total_cost_usd
        )
    
    def send_transaction(self, tx: Transaction, private_key: str) -> str:
        """Send transaction to blockchain"""
        if not self.web3:
            raise RuntimeError("Not connected to network")
        
        try:
            account: LocalAccount = Account.from_key(private_key)
            
            if account.address.lower() != tx.from_address.lower():
                raise ValueError("Private key does not match from_address")
            
            # Build transaction
            transaction = {
                'from': Web3.to_checksum_address(tx.from_address),
                'to': Web3.to_checksum_address(tx.to_address),
                'value': self.web3.to_wei(tx.amount, 'ether'),
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'chainId': self.web3.eth.chain_id
            }
            
            # Add EIP-1559 gas parameters
            latest_block = self.web3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', 0)
            
            try:
                max_priority_fee = self.web3.eth.max_priority_fee
            except:
                max_priority_fee = self.web3.to_wei(2, 'gwei')
            
            transaction['maxFeePerGas'] = base_fee * 2 + max_priority_fee
            transaction['maxPriorityFeePerGas'] = max_priority_fee
            
            # Estimate gas
            try:
                transaction['gas'] = self.web3.eth.estimate_gas(transaction)
            except:
                transaction['gas'] = 21000
            
            # Sign and send
            signed_txn = self.web3.eth.account.sign_transaction(
                transaction, private_key
            )
            tx_hash = self.web3.eth.send_raw_transaction(
                signed_txn.rawTransaction
            )
            
            logger.info(f"✅ ERC721 minted: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"❌ ERC721 mint failed: {e}")
            raise
    
    def get_erc721_owner(self, contract_address: str, token_id: int) -> str:
        """Get owner of ERC721 token"""
        if not self.web3:
            raise RuntimeError("Not connected to network")
        
        try:
            contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=self.ERC721_ABI
            )
            
            owner = contract.functions.ownerOf(token_id).call()
            return owner
            
        except Exception as e:
            logger.error(f"Error getting token owner: {e}")
            raise
    
    def transfer_erc721(self, contract_address: str, from_address: str,
                       to_address: str, token_id: int, private_key: str) -> str:
        """Transfer ERC721 NFT"""
        if not self.web3:
            raise RuntimeError("Not connected to network")
        
        try:
            contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=self.ERC721_ABI
            )
            
            account: LocalAccount = Account.from_key(private_key)
            
            transaction = contract.functions.transferFrom(
                Web3.to_checksum_address(from_address),
                Web3.to_checksum_address(to_address),
                token_id
            ).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'chainId': self.web3.eth.chain_id
            })
            
            latest_block = self.web3.eth.get_block('latest')
            transaction['maxFeePerGas'] = latest_block['baseFeePerGas'] * 2
            
            try:
                transaction['maxPriorityFeePerGas'] = self.web3.eth.max_priority_fee
            except:
                transaction['maxPriorityFeePerGas'] = self.web3.to_wei(2, 'gwei')
            
            try:
                transaction['gas'] = contract.functions.transferFrom(
                    Web3.to_checksum_address(from_address),
                    Web3.to_checksum_address(to_address),
                    token_id
                ).estimate_gas({'from': account.address})
            except:
                transaction['gas'] = 85000
            
            signed_txn = self.web3.eth.account.sign_transaction(
                transaction, private_key
            )
            tx_hash = self.web3.eth.send_raw_transaction(
                signed_txn.rawTransaction
            )
            
            logger.info(f"✅ ERC721 transferred: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"❌ ERC721 transfer failed: {e}")
            raise


# ============================================================================
# BLOCKCHAIN MANAGER
# ============================================================================

class BlockchainManager:
    """Production-ready blockchain manager"""
    
    def __init__(self):
        self.adapters: Dict[ChainType, BlockchainAdapter] = {}
        self.active_chain: Optional[ChainType] = None
        self.transaction_history: List[Transaction] = []
        self.contracts: Dict[str, SmartContract] = {}
        self.user_limits: TransactionLimits = TransactionLimits()
        self.price_oracle = PriceOracle()
        
        self._initialize_adapters()
        logger.info("BlockchainManager initialized")
    
    def _initialize_adapters(self):
        """Initialize blockchain adapters"""
        evm_chains = [
            ChainType.ETHEREUM, ChainType.ETHEREUM_SEPOLIA, 
            ChainType.ETHEREUM_HOLESKY, ChainType.POLYGON, 
            ChainType.POLYGON_AMOY
        ]
        
        for chain_type in evm_chains:
            self.adapters[chain_type] = EthereumAdapter(chain_type)
    
    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================
    
    def connect(self, chain: ChainType, network: str = "mainnet") -> bool:
        """Connect to blockchain"""
        if chain not in self.adapters:
            raise ValueError(f"Unsupported chain: {chain}")
        
        success = self.adapters[chain].connect(network)
        if success:
            self.active_chain = chain
        return success
    
    def disconnect(self):
        """Disconnect from current chain"""
        self.active_chain = None
        logger.info("Disconnected from blockchain")
    
    def switch_chain(self, chain: ChainType) -> bool:
        """Switch to different chain"""
        if chain not in self.adapters:
            return False
        self.active_chain = chain
        logger.info(f"Switched to {chain.value}")
        return True
    
    # ========================================================================
    # TRANSACTION LIMITS
    # ========================================================================
    
    def set_transaction_limits(self, limits: TransactionLimits):
        """Set user-defined transaction limits"""
        self.user_limits = limits
        logger.info("Transaction limits updated:")
        if limits.max_gas_price:
            logger.info(f"  Max gas price: {limits.max_gas_price} Gwei")
        if limits.max_total_cost:
            logger.info(f"  Max total cost: {limits.max_total_cost}")
        if limits.max_gas_limit:
            logger.info(f"  Max gas limit: {limits.max_gas_limit}")
    
    def get_transaction_limits(self) -> TransactionLimits:
        """Get current transaction limits"""
        return self.user_limits
    
    # ========================================================================
    # BALANCE & QUERIES
    # ========================================================================
    
    def get_balance(self, address: str, 
                   chain: Optional[ChainType] = None) -> float:
        """Get wallet balance"""
        chain = chain or self.active_chain
        if not chain:
            raise ValueError("No active chain selected")
        return self.adapters[chain].get_balance(address)
    
    def get_transaction(self, tx_hash: str, 
                       chain: Optional[ChainType] = None) -> Dict:
        """Get transaction details"""
        chain = chain or self.active_chain
        if not chain:
            raise ValueError("No active chain selected")
        return self.adapters[chain].get_transaction(tx_hash)
    
    def get_transaction_history(self, 
                               chain: Optional[ChainType] = None) -> List[Transaction]:
        """Get transaction history"""
        if chain:
            return [tx for tx in self.transaction_history if tx.chain == chain]
        return self.transaction_history
    
    # ========================================================================
    # GAS ESTIMATION
    # ========================================================================
    
    def estimate_transaction_cost(self, tx_type: str, 
                                  chain: Optional[ChainType] = None, 
                                  **params) -> GasEstimate:
        """Estimate transaction cost with limit checking"""
        chain = chain or self.active_chain
        if not chain:
            raise ValueError("No active chain selected")
        
        estimate = self.adapters[chain].estimate_gas(tx_type, **params)
        
        # Check limits
        exceeded = []
        
        if self.user_limits.max_gas_price and \
           estimate.recommended_gas_price > self.user_limits.max_gas_price:
            exceeded.append(
                f"Gas price {estimate.recommended_gas_price:.2f} Gwei exceeds "
                f"max {self.user_limits.max_gas_price:.2f} Gwei"
            )
        
        if self.user_limits.max_gas_limit and \
           estimate.estimated_gas > self.user_limits.max_gas_limit:
            exceeded.append(
                f"Gas limit {estimate.estimated_gas} exceeds "
                f"max {self.user_limits.max_gas_limit}"
            )
        
        if self.user_limits.max_total_cost and \
           estimate.total_cost_native > self.user_limits.max_total_cost:
            exceeded.append(
                f"Total cost {estimate.total_cost_native:.6f} exceeds "
                f"max {self.user_limits.max_total_cost:.6f}"
            )
        
        estimate.will_exceed_limits = len(exceeded) > 0
        estimate.exceeded_limits = exceeded
        
        return estimate
    
    # ========================================================================
    # NATIVE TOKEN TRANSACTIONS
    # ========================================================================
    
    def send_transaction(self, from_address: str, to_address: str, 
                        amount: float, private_key: str,
                        chain: Optional[ChainType] = None,
                        auto_estimate: bool = True,
                        force: bool = False) -> Transaction:
        """Send native token transaction with validation"""
        chain = chain or self.active_chain
        if not chain:
            raise ValueError("No active chain selected")
        
        if auto_estimate:
            estimate = self.estimate_transaction_cost(
                "transfer", chain=chain,
                from_address=from_address,
                to_address=to_address,
                amount=amount
            )
            
            currency = NETWORK_CONFIGS[chain].native_currency
            logger.info(f"💰 Transaction estimate: {estimate.total_cost_native:.6f} {currency}")
            
            if estimate.total_cost_usd:
                logger.info(f"   USD value: ${estimate.total_cost_usd:.2f}")
            
            if estimate.will_exceed_limits and not force:
                raise ValueError(
                    f"Transaction exceeds limits: {', '.join(estimate.exceeded_limits)}"
                )
        
        tx = Transaction(
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            chain=chain
        )
        
        self.adapters[chain].send_transaction(tx, private_key)
        self.transaction_history.append(tx)
        
        return tx
    
    def wait_for_transaction_receipt(self, tx_hash: str, 
                                    timeout: int = 120,
                                    chain: Optional[ChainType] = None) -> Dict:
        """Wait for transaction to be mined"""
        chain = chain or self.active_chain
        if not chain:
            raise ValueError("No active chain selected")
        
        adapter = self.adapters[chain]
        if isinstance(adapter, EthereumAdapter):
            try:
                receipt = adapter.web3.eth.wait_for_transaction_receipt(
                    tx_hash, timeout=timeout
                )
                return {
                    "transactionHash": receipt['transactionHash'].hex(),
                    "blockNumber": receipt['blockNumber'],
                    "gasUsed": receipt['gasUsed'],
                    "status": "success" if receipt['status'] == 1 else "failed"
                }
            except Exception as e:
                logger.error(f"Error waiting for receipt: {e}")
                raise
        else:
            raise NotImplementedError("Not implemented for this chain")
    
    # ========================================================================
    # SMART CONTRACTS
    # ========================================================================
    
    def deploy_contract(self, abi: List[Dict], bytecode: str, 
                       private_key: str,
                       chain: Optional[ChainType] = None) -> SmartContract:
        """Deploy smart contract"""
        chain = chain or self.active_chain
        if not chain:
            raise ValueError("No active chain selected")
        
        contract = SmartContract(
            address="",
            abi=abi,
            chain=chain,
            bytecode=bytecode
        )
        
        address = self.adapters[chain].deploy_contract(contract, private_key)
        contract.address = address
        self.contracts[address] = contract
        
        return contract
    
    # ========================================================================
    # ERC20 FUNCTIONS
    # ========================================================================
    
    def transfer_erc20(self, contract_address: str, from_address: str,
                      to_address: str, amount: int, private_key: str,
                      auto_estimate: bool = True, force: bool = False) -> str:
        """Transfer ERC20 tokens"""
        if not self.active_chain:
            raise ValueError("No active chain selected")
        
        evm_chains = [
            ChainType.ETHEREUM, ChainType.POLYGON,
            ChainType.ETHEREUM_SEPOLIA, ChainType.ETHEREUM_HOLESKY,
            ChainType.POLYGON_AMOY
        ]
        
        if self.active_chain not in evm_chains:
            raise ValueError(f"ERC20 not supported on {self.active_chain}")
        
        if auto_estimate:
            estimate = self.estimate_transaction_cost(
                "erc20_transfer",
                contract_address=contract_address,
                from_address=from_address,
                to_address=to_address,
                amount=amount
            )
            
            currency = NETWORK_CONFIGS[self.active_chain].native_currency
            logger.info(f"💸 ERC20 transfer cost: {estimate.total_cost_native:.6f} {currency}")
            
            if estimate.will_exceed_limits and not force:
                raise ValueError(
                    f"Transfer exceeds limits: {', '.join(estimate.exceeded_limits)}"
                )
        
        adapter = self.adapters[self.active_chain]
        return adapter.transfer_erc20(
            contract_address, from_address, to_address, amount, private_key
        )
    
    def get_erc20_balance(self, contract_address: str, 
                         wallet_address: str) -> int:
        """Get ERC20 token balance"""
        if not self.active_chain:
            raise ValueError("No active chain selected")
        
        adapter = self.adapters[self.active_chain]
        return adapter.get_erc20_balance(contract_address, wallet_address)
    
    # ========================================================================
    # ERC721 FUNCTIONS
    # ========================================================================
    
    def mint_erc721(self, contract_address: str, to_address: str,
                   token_id: int, private_key: str,
                   metadata_uri: str = "",
                   auto_estimate: bool = True, force: bool = False) -> str:
        """Mint ERC721 NFT"""
        if not self.active_chain:
            raise ValueError("No active chain selected")
        
        evm_chains = [
            ChainType.ETHEREUM, ChainType.POLYGON,
            ChainType.ETHEREUM_SEPOLIA, ChainType.ETHEREUM_HOLESKY,
            ChainType.POLYGON_AMOY
        ]
        
        if self.active_chain not in evm_chains:
            raise ValueError(f"ERC721 not supported on {self.active_chain}")
        
        if auto_estimate:
            estimate = self.estimate_transaction_cost(
                "erc721_mint",
                contract_address=contract_address,
                to_address=to_address,
                token_id=token_id
            )
            
            currency = NETWORK_CONFIGS[self.active_chain].native_currency
            logger.info(f"🎨 NFT mint cost: {estimate.total_cost_native:.6f} {currency}")
            
            if estimate.total_cost_usd:
                logger.info(f"   USD value: ${estimate.total_cost_usd:.2f}")
            
            if estimate.will_exceed_limits and not force:
                raise ValueError(
                    f"Mint exceeds limits: {', '.join(estimate.exceeded_limits)}"
                )
        
        adapter = self.adapters[self.active_chain]
        return adapter.mint_erc721(
            contract_address, to_address, token_id, private_key, metadata_uri
        )
    
    def get_erc721_owner(self, contract_address: str, token_id: int) -> str:
        """Get owner of ERC721 token"""
        if not self.active_chain:
            raise ValueError("No active chain selected")
        
        adapter = self.adapters[self.active_chain]
        return adapter.get_erc721_owner(contract_address, token_id)
    
    def transfer_erc721(self, contract_address: str, from_address: str,
                       to_address: str, token_id: int, private_key: str,
                       auto_estimate: bool = True, force: bool = False) -> str:
        """Transfer ERC721 NFT"""
        if not self.active_chain:
            raise ValueError("No active chain selected")
        
        if auto_estimate:
            estimate = self.estimate_transaction_cost(
                "erc721_transfer",
                contract_address=contract_address,
                from_address=from_address,
                to_address=to_address,
                token_id=token_id
            )
            
            if estimate.will_exceed_limits and not force:
                raise ValueError(
                    f"Transfer exceeds limits: {', '.join(estimate.exceeded_limits)}"
                )
        
        adapter = self.adapters[self.active_chain]
        return adapter.transfer_erc721(
            contract_address, from_address, to_address, token_id, private_key
        )
    
    
    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================
    
    def is_testnet(self, chain: Optional[ChainType] = None) -> bool:
        """Check if chain is testnet"""
        chain = chain or self.active_chain
        if not chain:
            raise ValueError("No active chain selected")
        return NETWORK_CONFIGS[chain].is_testnet
    
    def get_network_config(self, 
                          chain: Optional[ChainType] = None) -> NetworkConfig:
        """Get network configuration"""
        chain = chain or self.active_chain
        if not chain:
            raise ValueError("No active chain selected")
        return NETWORK_CONFIGS[chain]
    
    def get_faucet_url(self, chain: Optional[ChainType] = None) -> Optional[str]:
        """Get faucet URL for testnet"""
        chain = chain or self.active_chain
        if not chain:
            raise ValueError("No active chain selected")
        config = NETWORK_CONFIGS[chain]
        return config.faucet_url if config.is_testnet else None
    
    def list_testnets(self) -> List[ChainType]:
        """List available testnets"""
        return [c for c, cfg in NETWORK_CONFIGS.items() if cfg.is_testnet]
    
    def list_mainnets(self) -> List[ChainType]:
        """List available mainnets"""
        return [c for c, cfg in NETWORK_CONFIGS.items() if not cfg.is_testnet]
    
    def get_supported_chains(self) -> List[ChainType]:
        """Get all supported chains"""
        return list(self.adapters.keys())


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Production usage examples and testing
    """
    
    print("="*70)
    print("PRODUCTION BLOCKCHAIN MANAGER - COMPLETE VERSION")
    print("="*70)
    
    # Initialize manager
    manager = BlockchainManager()
    
    # Set transaction limits
    limits = TransactionLimits(
        max_gas_price=50.0,
        max_total_cost=0.01,
        max_gas_limit=300000
    )
    manager.set_transaction_limits(limits)
    
    print("\n✅ Manager initialized with transaction limits")
    print(f"   Max gas price: {limits.max_gas_price} Gwei")
    print(f"   Max total cost: {limits.max_total_cost} native currency")
    print(f"   Max gas limit: {limits.max_gas_limit} units")
    
    # List available networks
    print("\n" + "="*70)
    print("AVAILABLE NETWORKS")
    print("="*70)
    
    print("\n📡 Mainnets:")
    for chain in manager.list_mainnets():
        config = manager.get_network_config(chain)
        print(f"   • {chain.value.upper()} ({config.native_currency})")
    
    print("\n🧪 Testnets:")
    for chain in manager.list_testnets():
        config = manager.get_network_config(chain)
        print(f"   • {chain.value.upper()} ({config.native_currency})")
        if config.faucet_url:
            print(f"     💧 Get free tokens: {config.faucet_url}")
    
    # Example: Connect to testnet
    print("\n" + "="*70)
    print("CONNECTING TO SEPOLIA TESTNET")
    print("="*70)
    
    try:
        if manager.connect(ChainType.ETHEREUM_SEPOLIA):
            config = manager.get_network_config()
            print(f"\n🔍 Network Information:")
            print(f"   Chain ID: {config.chain_id}")
            print(f"   Native Currency: {config.native_currency}")
            print(f"   RPC URL: {config.rpc_url}")
            print(f"   Explorer: {config.explorer_url}")
            print(f"   Is Testnet: {config.is_testnet}")
            
            # Example balance check
            test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            print(f"\n💰 Balance Check:")
            try:
                balance = manager.get_balance(test_address)
                print(f"   Address: {test_address[:10]}...{test_address[-8:]}")
                print(f"   Balance: {balance:.6f} {config.native_currency}")
            except Exception as e:
                print(f"   ⚠️  Could not fetch balance: {str(e)[:50]}")
            
            # Example cost estimation
            print(f"\n📊 Cost Estimation (0.01 ETH transfer):")
            try:
                estimate = manager.estimate_transaction_cost(
                    "transfer",
                    from_address=test_address,
                    to_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEc",
                    amount=0.01
                )
                
                print(f"   Gas needed: {estimate.estimated_gas} units")
                print(f"   Gas price: {estimate.recommended_gas_price:.2f} Gwei")
                print(f"   Total cost: {estimate.total_cost_native:.6f} {config.native_currency}")
                print(f"   USD value: ${estimate.total_cost_usd or 0:.2f}")
                print(f"   Within limits: {'✅ Yes' if not estimate.will_exceed_limits else '❌ No'}")
                
                if estimate.will_exceed_limits:
                    print(f"\n   ⚠️  Exceeded limits:")
                    for limit in estimate.exceeded_limits:
                        print(f"      - {limit}")
            except Exception as e:
                print(f"   ⚠️  Could not estimate: {str(e)[:100]}")
    
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print(f"\nTroubleshooting:")
        print(f"   1. Check .env file exists with SEPOLIA_RPC_URL")
        print(f"   2. Verify RPC endpoint is accessible")
        print(f"   3. Try public RPC: https://rpc.sepolia.org")
    
    # Usage examples
    print("\n" + "="*70)
    print("USAGE EXAMPLES")
    print("="*70)
    
    print("""
1. SEND NATIVE TOKEN TRANSACTION:

   manager.connect(ChainType.ETHEREUM_SEPOLIA)
   
   tx = manager.send_transaction(
       from_address="0xYourAddress",
       to_address="0xRecipient",
       amount=0.001,  # 0.001 ETH
       private_key=os.getenv("WALLET_PRIVATE_KEY"),
       auto_estimate=True,
       force=False
   )
   
   print(f"Transaction: {tx.tx_hash}")
   
   # Wait for confirmation
   receipt = manager.wait_for_transaction_receipt(tx.tx_hash)
   print(f"Status: {receipt['status']}")


2. TRANSFER ERC20 TOKENS:

   # Amount in smallest unit (e.g., 1 USDC = 1000000 for 6 decimals)
   tx_hash = manager.transfer_erc20(
       contract_address="0xTokenContract",
       from_address="0xYourAddress",
       to_address="0xRecipient",
       amount=1000000000000000000,  # 1 token (18 decimals)
       private_key=os.getenv("WALLET_PRIVATE_KEY")
   )
   
   # Check balance
   balance = manager.get_erc20_balance(
       contract_address="0xTokenContract",
       wallet_address="0xYourAddress"
   )
   print(f"Balance: {balance}")


3. MINT NFT (ERC721):

   tx_hash = manager.mint_erc721(
       contract_address="0xNFTContract",
       to_address="0xRecipient",
       token_id=1,
       private_key=os.getenv("WALLET_PRIVATE_KEY"),
       metadata_uri="ipfs://QmYourMetadata",
       auto_estimate=True
   )
   
   # Verify ownership
   owner = manager.get_erc721_owner(
       contract_address="0xNFTContract",
       token_id=1
   )
   print(f"Owner: {owner}")


4. TRANSFER NFT:

   tx_hash = manager.transfer_erc721(
       contract_address="0xNFTContract",
       from_address="0xYourAddress",
       to_address="0xRecipient",
       token_id=1,
       private_key=os.getenv("WALLET_PRIVATE_KEY")
   )


5. DEPLOY SMART CONTRACT:

   contract = manager.deploy_contract(
       abi=contract_abi,
       bytecode=contract_bytecode,
       private_key=os.getenv("WALLET_PRIVATE_KEY")
   )
   
   print(f"Contract deployed at: {contract.address}")
""")
    
    # Security reminders
    print("\n" + "="*70)
    print("🔒 SECURITY BEST PRACTICES")
    print("="*70)
    
    print("""
✅ DO:
   • Store private keys in environment variables (.env)
   • Test on testnets before mainnet deployment
   • Set transaction limits to prevent overspending
   • Use hardware wallets for large amounts
   • Verify contract addresses before interaction
   • Monitor all transactions and set up alerts
   • Keep dependencies updated
   • Use authenticated RPC endpoints (Alchemy, Infura)

❌ DON'T:
   • Never hardcode private keys in source code
   • Never commit .env files to version control
   • Never skip gas estimation
   • Never ignore transaction limits
   • Never deploy to mainnet without thorough testing
   • Never expose API keys in public repositories
""")
    
    print("\n" + "="*70)
    print("🎉 SETUP COMPLETE")
    print("="*70)
    
    print("""
Next Steps:
1. Create .env file with your RPC URLs and API keys
2. Install dependencies: pip install web3 eth-account requests python-dotenv
3. Get testnet tokens from faucets
4. Test all functions on testnets
5. Deploy to production with proper security measures

Documentation: See docstrings in code for detailed API reference
Support: Check logs for error messages and troubleshooting
""")
    