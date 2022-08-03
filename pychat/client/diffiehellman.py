from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import secrets
import base64

# prime modulus (2048 bit) and base for diffie-hellman key exchange
PRIME = 32317006071311007300714876688669951960444102669715484032130345427524655138867890893197201411522913463688717960921898019494119559150490921095088152386448283120630877367300996091750197750389652106796057638384067568276792218642619756161838094338476170470581645852036305042887575891541065808607552399123930385521914333389668342420684974786564569494856176035326322058077805659331026192708460314150258592864177116725943603718461857357598351152334063994785580370721665417662212881203104945914551140008147396357886767669820042828793708588252247031092071155540224751031064253209884099238184688246467489498721336450133889385773
BASE = 5


def make_secret() -> int:
    return secrets.randbits(1024)


def make_public(secret: int) -> int:
    return pow(BASE, secret, PRIME)
        

def mix_keys(secret: int, public: int) -> int:
    """Mix the client's secret key with another public key"""
    return pow(public, secret, PRIME)
     

def create_fernet(key: int):
    """Use a secret key to create a Fernet for symmetric encryption"""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=None
    )
    k: bytes = hkdf.derive(key.to_bytes(256, 'big'))
    k: bytes = base64.urlsafe_b64encode(k)
    return Fernet(k)
