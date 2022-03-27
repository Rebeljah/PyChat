from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import secrets
import base64

from common import DH_BASE, DH_PRIME


class DHKeyGenerator:
    """Generate a private key and a public key and use other clients public
    keys to share secrets"""
    def __init__(self):
        self.secret: int = secrets.randbits(1024)
        self.public: int = pow(DH_BASE, self.secret, DH_PRIME)

    def mix_other(self, other_public: int) -> int:
        """Generate a shared secret"""
        return pow(other_public, self.secret, DH_PRIME)


def create_fernet(shared_secret: int):
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=None
    )
    key = hkdf.derive(shared_secret.to_bytes(256, 'big'))
    key = base64.urlsafe_b64encode(key)
    return Fernet(key)
