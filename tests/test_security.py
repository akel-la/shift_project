from app.core.security import create_token
from app.core.security import decode_token
from app.core.security import hash_password
from app.core.security import verify_password


def test_hash_and_verify():
    pwd = "secret"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed)
    assert not verify_password("wrong", hashed)


def test_create_and_decode_access_token():
    token = create_token(data={"sub": "1"}, token_type="access")
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["type"] == "access"


def test_create_and_decode_refresh_token():
    token = create_token(data={"sub": "2"}, token_type="refresh")
    payload = decode_token(token)
    assert payload["sub"] == "2"
    assert payload["type"] == "refresh"
