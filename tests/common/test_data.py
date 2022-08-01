import pytest
from cryptography.fernet import Fernet

from pychat.common.data import ChatMessage, EncryptedData
from pychat.client.encryption import create_fernet


@pytest.fixture
def fernet() -> Fernet:
    return create_fernet(1234)

@pytest.fixture
def chat_msg() -> ChatMessage:
    return ChatMessage('a channel id', 'fake_user', 'hello world')


def test_can_encrypt_and_decrypt(fernet, chat_msg):
    assert EncryptedData(chat_msg, fernet, '1234').decrypt(fernet) == chat_msg
