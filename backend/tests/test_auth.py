import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.auth.security import hash_password, verify_password, create_access_token, verify_access_token

def test_password_hashing():
    pwd = "SecretPassword123!"
    hashed = hash_password(pwd)
    
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_flow():
    token = create_access_token(user_id="user-123", email="alex@example.com")
    payload = verify_access_token(token)
    
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["email"] == "alex@example.com"
    
    # Tampered token check
    tampered = token[:-4] + "abcd"
    assert verify_access_token(tampered) is None

@pytest.mark.asyncio
async def test_auth_api_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"testuser_{int(pytest.importorskip('time').time())}@example.com"
        
        # 1. Signup
        signup_resp = await ac.post("/api/auth/signup", json={
            "email": email,
            "password": "Password12345",
            "full_name": "Test Candidate"
        })
        assert signup_resp.status_code == 200
        signup_data = signup_resp.json()
        assert signup_data["email"] == email
        assert "token" in signup_data
        
        # Duplicate signup should fail
        dup_resp = await ac.post("/api/auth/signup", json={
            "email": email,
            "password": "Password12345",
            "full_name": "Test Candidate"
        })
        assert dup_resp.status_code == 400

        # 2. Login
        login_resp = await ac.post("/api/auth/login", json={
            "email": email,
            "password": "Password12345"
        })
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        token = login_data["token"]
        assert token

        # Invalid login
        bad_login = await ac.post("/api/auth/login", json={
            "email": email,
            "password": "WrongPassword"
        })
        assert bad_login.status_code == 401

        # 3. Profile /me
        me_resp = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["email"] == email
        assert me_data["full_name"] == "Test Candidate"
