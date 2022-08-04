
from pychat.common.protocol import Encryptable, StreamData, register_models, json_to_model


class NestedData(StreamData):
        data: int
        
class TestData(Encryptable):
    data: str
    nested: NestedData

register_models(StreamData)

def test_can_encrypt_and_decrypt(fernet):
    m = TestData(data='hello')
    assert m.encrypt(fernet, '').decrypt(fernet) == m


def test_can_serialize_and_parse():
    m = TestData(
        data='hello',
        nested=NestedData(data=777)
    )
    assert json_to_model(m.json()) == m
