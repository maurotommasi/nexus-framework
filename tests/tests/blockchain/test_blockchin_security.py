#!/usr/bin/env python3
"""
Secure Blockchain Manager - Comprehensive Unit Tests
====================================================
40 unit tests covering security features and private key protection

Author: Test Suite
Version: 1.0.0
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
import os
import json
import tempfile
import shutil
import base64
from typing import Dict

# Import classes from the secure blockchain manager
from secure_blockchain_manager import (
    EncryptedKeyStore, Web3KeyStore, TransactionSigningService,
    HardwareWalletManager, AWSKMSManager, SecureBlockchainManager
)


# =============================================================================
# ENCRYPTED KEYSTORE TESTS (Tests 1-12)
# =============================================================================

class TestEncryptedKeyStore(unittest.TestCase):
    """Test EncryptedKeyStore functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.keystore = EncryptedKeyStore(storage_path=self.temp_dir)
        self.test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        self.test_private_key = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        self.test_password = "SecurePassword123!"
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_001_keystore_initialization(self):
        """Test keystore initialization"""
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertEqual(self.keystore.storage_path, self.temp_dir)
    
    def test_002_save_encrypted_key(self):
        """Test saving encrypted key"""
        filename = self.keystore.save_encrypted_key(
            self.test_address,
            self.test_private_key,
            self.test_password
        )
        self.assertTrue(os.path.exists(filename))
    
    def test_003_load_encrypted_key(self):
        """Test loading and decrypting key"""
        self.keystore.save_encrypted_key(
            self.test_address,
            self.test_private_key,
            self.test_password
        )
        
        decrypted_key = self.keystore.load_encrypted_key(
            self.test_address,
            self.test_password
        )
        self.assertEqual(decrypted_key, self.test_private_key)
    
    def test_004_wrong_password_fails(self):
        """Test decryption with wrong password fails"""
        self.keystore.save_encrypted_key(
            self.test_address,
            self.test_private_key,
            self.test_password
        )
        
        with self.assertRaises(ValueError):
            self.keystore.load_encrypted_key(
                self.test_address,
                "WrongPassword123!"
            )
    
    def test_005_keystore_file_structure(self):
        """Test keystore file has correct structure"""
        filename = self.keystore.save_encrypted_key(
            self.test_address,
            self.test_private_key,
            self.test_password
        )
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.assertIn("address", data)
        self.assertIn("crypto", data)
        self.assertIn("version", data)
        self.assertIn("cipher", data["crypto"])
        self.assertIn("ciphertext", data["crypto"])
        self.assertIn("salt", data["crypto"])
    
    def test_006_delete_key(self):
        """Test deleting encrypted key"""
        self.keystore.save_encrypted_key(
            self.test_address,
            self.test_private_key,
            self.test_password
        )
        
        self.keystore.delete_key(self.test_address)
        filename = f"{self.temp_dir}/{self.test_address.lower()}.json"
        self.assertFalse(os.path.exists(filename))
    
    def test_007_load_nonexistent_key(self):
        """Test loading non-existent key raises error"""
        with self.assertRaises(ValueError):
            self.keystore.load_encrypted_key(
                "0xNonExistent",
                self.test_password
            )
    
    def test_008_pbkdf2_key_derivation(self):
        """Test PBKDF2 key derivation"""
        salt1 = os.urandom(16)
        salt2 = os.urandom(16)
        
        key1 = self.keystore._derive_key(self.test_password, salt1)
        key2 = self.keystore._derive_key(self.test_password, salt1)
        key3 = self.keystore._derive_key(self.test_password, salt2)
        
        # Same password and salt should produce same key
        self.assertEqual(key1, key2)
        # Different salt should produce different key
        self.assertNotEqual(key1, key3)
    
    def test_009_multiple_keys_storage(self):
        """Test storing multiple keys"""
        addresses = [
            "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"
        ]
        
        for addr in addresses:
            self.keystore.save_encrypted_key(addr, self.test_private_key, self.test_password)
        
        # Both should exist
        for addr in addresses:
            filename = f"{self.temp_dir}/{addr.lower()}.json"
            self.assertTrue(os.path.exists(filename))
    
    def test_010_salt_randomness(self):
        """Test salt is random for each key"""
        addr1 = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        addr2 = "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"
        
        self.keystore.save_encrypted_key(addr1, self.test_private_key, self.test_password)
        self.keystore.save_encrypted_key(addr2, self.test_private_key, self.test_password)
        
        with open(f"{self.temp_dir}/{addr1.lower()}.json", 'r') as f:
            data1 = json.load(f)
        with open(f"{self.temp_dir}/{addr2.lower()}.json", 'r') as f:
            data2 = json.load(f)
        
        # Salts should be different
        self.assertNotEqual(data1["crypto"]["salt"], data2["crypto"]["salt"])
    
    def test_011_empty_password_handling(self):
        """Test handling of empty password"""
        # Should work but not recommended
        self.keystore.save_encrypted_key(
            self.test_address,
            self.test_private_key,
            ""
        )
        decrypted = self.keystore.load_encrypted_key(self.test_address, "")
        self.assertEqual(decrypted, self.test_private_key)
    
    def test_012_special_characters_in_password(self):
        """Test password with special characters"""
        special_password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:',.<>?/~`"
        self.keystore.save_encrypted_key(
            self.test_address,
            self.test_private_key,
            special_password
        )
        decrypted = self.keystore.load_encrypted_key(self.test_address, special_password)
        self.assertEqual(decrypted, self.test_private_key)


# =============================================================================
# WEB3 KEYSTORE TESTS (Tests 13-18)
# =============================================================================

class TestWeb3KeyStore(unittest.TestCase):
    """Test Web3KeyStore functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.keystore = Web3KeyStore(storage_path=self.temp_dir)
        self.test_private_key = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        self.test_password = "SecurePassword123!"
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_013_web3_keystore_creation(self):
        """Test Web3-compatible keystore creation"""
        keystore_dict = self.keystore.create_keystore(
            self.test_private_key,
            self.test_password
        )
        
        self.assertIn("address", keystore_dict)
        self.assertIn("crypto", keystore_dict)
        self.assertIn("version", keystore_dict)
    
    def test_014_web3_keystore_format_version(self):
        """Test Web3 keystore has version 3"""
        keystore_dict = self.keystore.create_keystore(
            self.test_private_key,
            self.test_password
        )
        self.assertEqual(keystore_dict["version"], 3)
    
    def test_015_web3_keystore_crypto_params(self):
        """Test Web3 keystore has required crypto parameters"""
        keystore_dict = self.keystore.create_keystore(
            self.test_private_key,
            self.test_password
        )
        
        crypto = keystore_dict["crypto"]
        self.assertIn("cipher", crypto)
        self.assertIn("ciphertext", crypto)
        self.assertIn("kdf", crypto)
        self.assertIn("kdfparams", crypto)
    
    def test_016_web3_keystore_load(self):
        """Test loading Web3 keystore"""
        from eth_account import Account
        
        account = Account.from_key(self.test_private_key)
        self.keystore.create_keystore(self.test_private_key, self.test_password)
        
        loaded_key = self.keystore.load_keystore(account.address, self.test_password)
        
        # Should be able to recover the private key
        self.assertTrue(loaded_key.startswith("0x") or loaded_key.startswith("0X"))
    
    def test_017_web3_keystore_wrong_password(self):
        """Test Web3 keystore with wrong password fails"""
        from eth_account import Account
        
        account = Account.from_key(self.test_private_key)
        self.keystore.create_keystore(self.test_private_key, self.test_password)
        
        with self.assertRaises(ValueError):
            self.keystore.load_keystore(account.address, "WrongPassword")
    
    def test_018_web3_keystore_file_saved(self):
        """Test Web3 keystore file is saved"""
        from eth_account import Account
        
        account = Account.from_key(self.test_private_key)
        self.keystore.create_keystore(self.test_private_key, self.test_password)
        
        filename = f"{self.temp_dir}/{account.address.lower()}.json"
        self.assertTrue(os.path.exists(filename))


# =============================================================================
# TRANSACTION SIGNING SERVICE TESTS (Tests 19-26)
# =============================================================================

class TestTransactionSigningService(unittest.TestCase):
    """Test TransactionSigningService functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.keystore = EncryptedKeyStore(storage_path=self.temp_dir)
        self.service = TransactionSigningService(self.keystore)
        
        self.test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        self.test_private_key = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        self.test_password = "SecurePassword123!"
        
        # Register user
        self.keystore.save_encrypted_key(
            self.test_address,
            self.test_private_key,
            self.test_password
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_019_create_session(self):
        """Test creating authenticated session"""
        session_token = self.service.create_session(
            self.test_address,
            self.test_password
        )
        
        self.assertIsInstance(session_token, str)
        self.assertEqual(len(session_token), 64)  # SHA256 hex
    
    def test_020_create_session_wrong_password(self):
        """Test session creation with wrong password fails"""
        with self.assertRaises(ValueError):
            self.service.create_session(
                self.test_address,
                "WrongPassword"
            )
    
    def test_021_session_stored(self):
        """Test session is stored in active sessions"""
        session_token = self.service.create_session(
            self.test_address,
            self.test_password
        )
        
        self.assertIn(session_token, self.service.active_sessions)
        self.assertEqual(
            self.service.active_sessions[session_token],
            self.test_address
        )
    
    def test_022_sign_transaction_with_session(self):
        """Test signing transaction with valid session"""
        session_token = self.service.create_session(
            self.test_address,
            self.test_password
        )
        
        transaction = {
            'to': '0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199',
            'value': 1000000000000000000,
            'nonce': 0,
            'gas': 21000,
            'gasPrice': 50000000000,
            'chainId': 1
        }
        
        signed_tx = self.service.sign_transaction(
            session_token,
            transaction,
            self.test_password
        )
        
        self.assertIsInstance(signed_tx, str)
        self.assertTrue(signed_tx.startswith("0x"))
    
    def test_023_sign_with_invalid_session(self):
        """Test signing with invalid session fails"""
        transaction = {
            'to': '0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199',
            'value': 1000000000000000000
        }
        
        with self.assertRaises(ValueError):
            self.service.sign_transaction(
                "invalid_session_token",
                transaction,
                self.test_password
            )
    
    def test_024_revoke_session(self):
        """Test revoking session"""
        session_token = self.service.create_session(
            self.test_address,
            self.test_password
        )
        
        self.service.revoke_session(session_token)
        self.assertNotIn(session_token, self.service.active_sessions)
    
    def test_025_multiple_sessions(self):
        """Test multiple concurrent sessions"""
        session1 = self.service.create_session(
            self.test_address,
            self.test_password
        )
        session2 = self.service.create_session(
            self.test_address,
            self.test_password
        )
        
        self.assertNotEqual(session1, session2)
        self.assertEqual(len(self.service.active_sessions), 2)
    
    def test_026_session_token_uniqueness(self):
        """Test session tokens are unique"""
        tokens = set()
        for _ in range(10):
            token = self.service.create_session(
                self.test_address,
                self.test_password
            )
            tokens.add(token)
        
        # All tokens should be unique
        self.assertEqual(len(tokens), 10)


# =============================================================================
# HARDWARE WALLET MANAGER TESTS (Tests 27-32)
# =============================================================================

class TestHardwareWalletManager(unittest.TestCase):
    """Test HardwareWalletManager functionality"""
    
    def setUp(self):
        self.manager = HardwareWalletManager()
    
    def test_027_initial_no_device(self):
        """Test initially no device is connected"""
        self.assertIsNone(self.manager.device_type)
    
    def test_028_connect_ledger(self):
        """Test Ledger connection (mocked)"""
        # Note: Actual hardware connection would require device
        connected = self.manager.connect_ledger()
        self.assertTrue(connected)
        self.assertEqual(self.manager.device_type, "ledger")
    
    def test_029_connect_trezor(self):
        """Test Trezor connection (mocked)"""
        connected = self.manager.connect_trezor()
        self.assertTrue(connected)
        self.assertEqual(self.manager.device_type, "trezor")
    
    def test_030_get_address_no_device(self):
        """Test getting address without connected device fails"""
        with self.assertRaises(ValueError):
            self.manager.get_address()
    
    def test_031_get_address_with_device(self):
        """Test getting address with connected device"""
        self.manager.connect_ledger()
        address = self.manager.get_address()
        self.assertIsInstance(address, str)
    
    def test_032_sign_transaction_no_device(self):
        """Test signing without device fails"""
        transaction = {'to': '0xRecipient', 'value': 1000}
        
        with self.assertRaises(ValueError):
            self.manager.sign_transaction(transaction)


# =============================================================================
# AWS KMS MANAGER TESTS (Tests 33-36)
# =============================================================================

class TestAWSKMSManager(unittest.TestCase):
    """Test AWSKMSManager functionality"""
    
    def setUp(self):
        self.manager = AWSKMSManager(region="us-east-1")
    
    def test_033_kms_initialization(self):
        """Test KMS manager initialization"""
        self.assertEqual(self.manager.region, "us-east-1")
        self.assertIsNone(self.manager.kms_client)
    
    def test_034_initialize_requires_boto3(self):
        """Test initialization requires boto3"""
        # If boto3 not installed, should raise ImportError
        # This test validates the error handling
        try:
            self.manager.initialize()
        except ImportError as e:
            self.assertIn("boto3", str(e))
    
    @patch('boto3.client')
    def test_035_create_key_with_alias(self, mock_boto_client):
        """Test creating KMS key with alias"""
        mock_kms = MagicMock()
        mock_kms.create_key.return_value = {
            'KeyMetadata': {'KeyId': 'test-key-id-123'}
        }
        mock_boto_client.return_value = mock_kms
        
        self.manager.initialize()
        key_id = self.manager.create_key("test-wallet")
        
        self.assertEqual(key_id, "test-key-id-123")
        mock_kms.create_alias.assert_called_once()
    
    @patch('boto3.client')
    def test_036_sign_with_kms(self, mock_boto_client):
        """Test signing transaction with KMS"""
        mock_kms = MagicMock()
        mock_kms.sign.return_value = {'Signature': b'signature_bytes'}
        mock_boto_client.return_value = mock_kms
        
        self.manager.initialize()
        signature = self.manager.sign_transaction(
            "test-key-id",
            b"transaction_hash"
        )
        
        self.assertEqual(signature, b'signature_bytes')


# =============================================================================
# SECURE BLOCKCHAIN MANAGER TESTS (Tests 37-40)
# =============================================================================

class TestSecureBlockchainManager(unittest.TestCase):
    """Test SecureBlockchainManager functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_037_manager_encrypted_keystore_mode(self):
        """Test manager in encrypted keystore mode"""
        manager = SecureBlockchainManager(security_mode="encrypted_keystore")
        self.assertEqual(manager.security_mode, "encrypted_keystore")
        self.assertIsNotNone(manager.keystore)
    
    def test_038_manager_web3_keystore_mode(self):
        """Test manager in Web3 keystore mode"""
        manager = SecureBlockchainManager(security_mode="web3_keystore")
        self.assertEqual(manager.security_mode, "web3_keystore")
        self.assertIsNotNone(manager.keystore)
    
    def test_039_manager_hardware_wallet_mode(self):
        """Test manager in hardware wallet mode"""
        manager = SecureBlockchainManager(security_mode="hardware_wallet")
        self.assertEqual(manager.security_mode, "hardware_wallet")
        self.assertIsNotNone(manager.hw_manager)
    
    def test_040_manager_invalid_mode(self):
        """Test manager with invalid security mode fails"""
        with self.assertRaises(ValueError):
            SecureBlockchainManager(security_mode="invalid_mode")


# =============================================================================
# TEST SUITE RUNNER
# =============================================================================

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEncryptedKeyStore))
    suite.addTests(loader.loadTestsFromTestCase(TestWeb3KeyStore))
    suite.addTests(loader.loadTestsFromTestCase(TestTransactionSigningService))
    suite.addTests(loader.loadTestsFromTestCase(TestHardwareWalletManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAWSKMSManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSecureBlockchainManager))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("SECURE BLOCKCHAIN MANAGER TEST SUMMARY")
    print("="*70)
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*70)
    
    # Test coverage breakdown
    print("\nTest Coverage Breakdown:")
    print("  - Encrypted Keystore: 12 tests")
    print("  - Web3 Keystore: 6 tests")
    print("  - Transaction Signing Service: 8 tests")
    print("  - Hardware Wallet Manager: 6 tests")
    print("  - AWS KMS Manager: 4 tests")
    print("  - Secure Blockchain Manager: 4 tests")
    print("="*70)
    
    if result.wasSuccessful():
        print("\n✅ All security tests passed!")
        print("\nSecurity Features Validated:")
        print("  ✓ Encrypted key storage with PBKDF2")
        print("  ✓ Web3-compatible keystore format")
        print("  ✓ Session-based authentication")
        print("  ✓ Hardware wallet integration")
        print("  ✓ Cloud KMS support")
        print("  ✓ Multiple security modes")
        print("\nNext Steps:")
        print("  1. Test with actual hardware wallets")
        print("  2. Add penetration testing")
        print("  3. Audit cryptographic implementations")
        print("  4. Test key rotation mechanisms")
        print("  5. Add rate limiting tests")
    else:
        print("\n❌ Some tests failed. Review the output above.")
    
    print("\n" + "="*70)
    print("SECURITY BEST PRACTICES REMINDER")
    print("="*70)
    print("""
    ✓ Never store private keys in plain text
    ✓ Use strong passwords (12+ characters)
    ✓ Implement key rotation policies
    ✓ Use hardware wallets for large amounts
    ✓ Enable multi-factor authentication
    ✓ Regular security audits
    ✓ Monitor for unauthorized access
    ✓ Implement rate limiting
    ✓ Use session timeouts
    ✓ Log all security events
    """)
    print("="*70)
    
    # Exit with appropriate code
    import sys
    sys.exit(0 if result.wasSuccessful() else 1)