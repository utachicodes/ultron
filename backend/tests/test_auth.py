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


def _register_and_login(anon, email: str, password: str = "supersecret"):
    registered = anon.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert registered.status_code == 200, registered.text
    login = anon.post(
        "/auth/token",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return registered.json(), login.json()["access_token"]


def test_change_password_rotates_credentials(anon, db):
    user, token = _register_and_login(anon, "rotate@user.sn")
    headers = {"Authorization": f"Bearer {token}"}

    res = anon.post(
        "/auth/change-password",
        headers=headers,
        json={"current_password": "supersecret", "new_password": "a-longer-secret-42"},
    )
    assert res.status_code == 200, res.text
    assert res.json() == {"changed": True}

    assert anon.post(
        "/auth/token",
        json={"email": "rotate@user.sn", "password": "supersecret"},
    ).status_code == 400
    assert anon.post(
        "/auth/token",
        json={"email": "rotate@user.sn", "password": "a-longer-secret-42"},
    ).status_code == 200

    from app import models
    entry = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.action == "change_password",
            models.AuditLog.user_id == user["id"],
        )
        .first()
    )
    assert entry is not None
    assert "a-longer-secret-42" not in (entry.details or "")


def test_change_password_rejects_wrong_current_password(anon):
    _, token = _register_and_login(anon, "wrong-current@user.sn")
    res = anon.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "not-my-password", "new_password": "a-longer-secret-42"},
    )
    assert res.status_code == 400
    assert "Current password" in res.json()["detail"]


def test_change_password_rejects_short_or_reused_password(anon):
    _, token = _register_and_login(anon, "policy@user.sn")
    headers = {"Authorization": f"Bearer {token}"}

    short = anon.post(
        "/auth/change-password",
        headers=headers,
        json={"current_password": "supersecret", "new_password": "short"},
    )
    assert short.status_code == 422

    reused = anon.post(
        "/auth/change-password",
        headers=headers,
        json={"current_password": "supersecret", "new_password": "supersecret"},
    )
    assert reused.status_code == 400


def test_change_password_requires_authentication(anon):
    res = anon.post(
        "/auth/change-password",
        json={"current_password": "supersecret", "new_password": "a-longer-secret-42"},
    )
    assert res.status_code == 401


def test_admin_can_reset_a_password(client, anon, db):
    user, _ = _register_and_login(anon, "reset-me@user.sn")

    res = client.post(f"/admin/users/{user['id']}/reset-password")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["email"] == "reset-me@user.sn"
    assert body["user_id"] == user["id"]
    temp = body["temporary_password"]
    assert len(temp) >= 16

    assert anon.post(
        "/auth/token",
        json={"email": "reset-me@user.sn", "password": "supersecret"},
    ).status_code == 400
    assert anon.post(
        "/auth/token",
        json={"email": "reset-me@user.sn", "password": temp},
    ).status_code == 200

    from app import models
    entry = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.action == "admin_reset_password")
        .first()
    )
    assert entry is not None
    assert temp not in (entry.details or "")


def test_admin_can_create_a_user_with_any_role(client, anon, db):
    res = client.post(
        "/admin/users",
        json={"email": "new-analyst@ultorn.local", "password": "analyst-pass-1", "role": "analyst"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["role"] == "analyst"
    assert body["is_active"] is True

    login = anon.post(
        "/auth/token",
        json={"email": "new-analyst@ultorn.local", "password": "analyst-pass-1"},
    )
    assert login.status_code == 200

    from app import models
    entry = db.query(models.AuditLog).filter(models.AuditLog.action == "admin_create_user").first()
    assert entry is not None
    assert "analyst-pass-1" not in (entry.details or "")


def test_admin_create_user_rejects_duplicate_email(client):
    client.post("/admin/users", json={"email": "dup@ultorn.local", "password": "password1"})
    res = client.post("/admin/users", json={"email": "dup@ultorn.local", "password": "password2"})
    assert res.status_code == 400


def test_non_admin_cannot_create_a_user(anon):
    _, token = _register_and_login(anon, "not-admin-2@user.sn")
    res = anon.post(
        "/admin/users",
        json={"email": "sneaky@user.sn", "password": "password1", "role": "admin"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_non_admin_cannot_reset_a_password(anon):
    user, token = _register_and_login(anon, "not-admin@user.sn")
    victim, _ = _register_and_login(anon, "victim@user.sn")

    res = anon.post(
        f"/admin/users/{victim['id']}/reset-password",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_disabled_account_cannot_sign_in_or_reuse_its_token(client, anon):
    user, token = _register_and_login(anon, "disabled@user.sn")
    headers = {"Authorization": f"Bearer {token}"}

    assert anon.get("/auth/me", headers=headers).status_code == 200
    assert client.patch(
        f"/admin/users/{user['id']}", json={"is_active": False}
    ).status_code == 200

    assert anon.get("/auth/me", headers=headers).status_code == 401
    assert anon.post(
        "/auth/token",
        json={"email": "disabled@user.sn", "password": "supersecret"},
    ).status_code == 400

    assert client.patch(
        f"/admin/users/{user['id']}", json={"is_active": True}
    ).status_code == 200
    assert anon.post(
        "/auth/token",
        json={"email": "disabled@user.sn", "password": "supersecret"},
    ).status_code == 200


def test_forgot_password_issues_a_token_in_debug_mode(anon, db):
    _register_and_login(anon, "forgetful@user.sn")

    res = anon.post("/auth/forgot-password", json={"email": "forgetful@user.sn"})
    assert res.status_code == 200
    token = res.json()["dev_reset_token"]
    assert token

    from app import models
    entry = db.query(models.AuditLog).filter(
        models.AuditLog.action == "forgot_password_requested",
    ).first()
    assert entry is not None


def test_forgot_password_does_not_leak_account_existence(anon):
    exists = anon.post("/auth/forgot-password", json={"email": "forgetful@user.sn"})
    missing = anon.post("/auth/forgot-password", json={"email": "nobody-here@user.sn"})
    assert exists.status_code == missing.status_code == 200
    assert exists.json()["detail"] == missing.json()["detail"]
    assert "dev_reset_token" not in missing.json()


def test_reset_password_with_valid_token(anon, db):
    _register_and_login(anon, "reset-flow@user.sn")
    token = anon.post(
        "/auth/forgot-password", json={"email": "reset-flow@user.sn"}
    ).json()["dev_reset_token"]

    res = anon.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "brand-new-secret-9"},
    )
    assert res.status_code == 200, res.text

    assert anon.post(
        "/auth/token",
        json={"email": "reset-flow@user.sn", "password": "supersecret"},
    ).status_code == 400
    assert anon.post(
        "/auth/token",
        json={"email": "reset-flow@user.sn", "password": "brand-new-secret-9"},
    ).status_code == 200

    from app import models
    entry = db.query(models.AuditLog).filter(
        models.AuditLog.action == "reset_password",
    ).first()
    assert entry is not None


def test_reset_password_token_is_single_use(anon):
    _register_and_login(anon, "one-shot@user.sn")
    token = anon.post(
        "/auth/forgot-password", json={"email": "one-shot@user.sn"}
    ).json()["dev_reset_token"]

    first = anon.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "brand-new-secret-9"},
    )
    assert first.status_code == 200

    second = anon.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "another-secret-10"},
    )
    assert second.status_code == 400


def test_reset_password_rejects_unknown_token(anon):
    res = anon.post(
        "/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": "brand-new-secret-9"},
    )
    assert res.status_code == 400


def test_requesting_a_new_reset_token_invalidates_the_previous_one(anon):
    _register_and_login(anon, "re-request@user.sn")
    first_token = anon.post(
        "/auth/forgot-password", json={"email": "re-request@user.sn"}
    ).json()["dev_reset_token"]
    second_token = anon.post(
        "/auth/forgot-password", json={"email": "re-request@user.sn"}
    ).json()["dev_reset_token"]

    assert anon.post(
        "/auth/reset-password",
        json={"token": first_token, "new_password": "brand-new-secret-9"},
    ).status_code == 400
    assert anon.post(
        "/auth/reset-password",
        json={"token": second_token, "new_password": "brand-new-secret-9"},
    ).status_code == 200
