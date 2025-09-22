from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from pathlib import Path

class Security:
    """Handles RSA asymmetric encryption and decryption."""

    def __init__(self, private_key_file: str = "private_key.pem", public_key_file: str = "public_key.pem", key_size: int = 4096):
        self.private_key_file = Path(private_key_file)
        self.public_key_file = Path(public_key_file)
        self.key_size = key_size
        self.private_key = None
        self.public_key = None
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones if they don't exist."""
        if self.private_key_file.exists() and self.public_key_file.exists():
            with open(self.private_key_file, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
            with open(self.public_key_file, "rb") as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
        else:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.key_size,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
            # Save keys to files
            with open(self.private_key_file, "wb") as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            with open(self.public_key_file, "wb") as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))

    def encrypt(self, message: str) -> bytes:
        """Encrypt a message using the public key."""
        if not self.public_key:
            raise ValueError("Public key not loaded")
        ciphertext = self.public_key.encrypt(
            message.encode("utf-8"),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext

    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt a message using the private key."""
        if not self.private_key:
            raise ValueError("Private key not loaded")
        plaintext = self.private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode("utf-8")
