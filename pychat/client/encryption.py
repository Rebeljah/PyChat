from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import secrets
import base64

# prime modulus (2048 bit) and base for diffie-hellman key exchange
DH_PRIME = 32317006071311007300714876688669951960444102669715484032130345427524655138867890893197201411522913463688717960921898019494119559150490921095088152386448283120630877367300996091750197750389652106796057638384067568276792218642619756161838094338476170470581645852036305042887575891541065808607552399123930385521914333389668342420684974786564569494856176035326322058077805659331026192708460314150258592864177116725943603718461857357598351152334063994785580370721665417662212881203104945914551140008147396357886767669820042828793708588252247031092071155540224751031064253209884099238184688246467489498721336450133889385773
DH_BASE = 5


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
