import pytest

from pychat.client.encryption import create_fernet
from pychat.common.data import ChatMessage


@pytest.fixture
def stream_data() -> ChatMessage:
    return ChatMessage('chanid', 'fakeuser', 'hello world')


@pytest.fixture
def fernet():
    return create_fernet(123478686)