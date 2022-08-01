import pytest
from cryptography.fernet import Fernet

from pychat.common.data import EncryptedData


def test_can_encrypt_and_decrypt(fernet, stream_data):
    assert EncryptedData(stream_data, fernet, '1234').decrypt(fernet) == stream_data
