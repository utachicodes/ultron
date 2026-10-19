from __future__ import annotations


def test_health(anon):
    res = anon.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_root_is_never_a_bare_404(anon):
    res = anon.get("/")
    assert res.status_code == 200
    assert res.json()["docs"] == "/docs"


def test_unrouted_path_gets_a_hint(anon):
    res = anon.get("/v1/models")
    assert res.status_code == 404
    body = res.json()
    assert body["detail"] == "Not Found"
    assert body["path"] == "/v1/models"
    assert "docs" in body


def test_domain_404_detail_is_preserved(client):
    res = client.get("/clients/99999")
    assert res.status_code == 404
    assert res.json() == {"detail": "Client not found"}


def test_register_defaults_to_client_role(anon, db):
    res = anon.post(
        "/auth/register",
        json={"email": "new@user.sn", "password": "supersecret", "full_name": "New User"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["role"] == "client"
    assert body["email"] == "new@user.sn"
    assert "hashed_password" not in body


def test_register_cannot_self_assign_admin(anon):
    res = anon.post(
        "/auth/register",
        json={"email": "evil@user.sn", "password": "supersecret", "role": "admin"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["role"] == "client"


def test_login_and_me(anon):
    anon.post(
        "/auth/register",
        json={"email": "login@user.sn", "password": "supersecret"},
    )
    res = anon.post(
        "/auth/token",
        json={"email": "login@user.sn", "password": "supersecret"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]

    me = anon.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "login@user.sn"


def test_login_rejects_bad_password(anon):
    anon.post(
        "/auth/register",
        json={"email": "bad@user.sn", "password": "supersecret"},
    )
    res = anon.post(
        "/auth/token",
        json={"email": "bad@user.sn", "password": "wrong"},
    )
    assert res.status_code == 400


def test_protected_route_requires_token(anon):
    assert anon.get("/clients").status_code == 401


def test_login_is_rate_limited(anon):
    codes = []
    for _ in range(12):
        codes.append(
            anon.post(
                "/auth/token",
                json={"email": "nobody@user.sn", "password": "nope"},
            ).status_code
        )
    assert 429 in codes
    # first attempt should still be a normal credential failure
    assert codes[0] == 400
