from __future__ import annotations

"""Tests for the missing-authorization-check detector in app/code_scanner.py.

A heuristic signal (not a proof like authz_hunter's role-replay findings):
flags a route definition with no visible auth check in a short window
around it. These tests pin that behavior down precisely so the heuristic
doesn't silently drift.
"""

from app.code_scanner import scan_content


def test_flags_fastapi_route_with_no_auth_check():
    code = (
        "@app.get('/admin/users')\n"
        "def list_users():\n"
        "    return db.query(User).all()\n"
    )
    issues = scan_content(code, "views.py")
    missing = [i for i in issues if i["issue_type"] == "missing_authz_check"]
    assert len(missing) == 1
    assert missing[0]["line_number"] == 1
    assert missing[0]["severity"] == "medium"


def test_does_not_flag_fastapi_route_with_depends_auth():
    code = (
        "@app.get('/admin/users')\n"
        "def list_users(current_user: User = Depends(get_current_user)):\n"
        "    return db.query(User).all()\n"
    )
    issues = scan_content(code, "views.py")
    assert not any(i["issue_type"] == "missing_authz_check" for i in issues)


def test_does_not_flag_route_with_login_required_decorator():
    code = (
        "@app.route('/dashboard')\n"
        "@login_required\n"
        "def dashboard():\n"
        "    return render_template('dashboard.html')\n"
    )
    issues = scan_content(code, "views.py")
    assert not any(i["issue_type"] == "missing_authz_check" for i in issues)


def test_flags_express_style_route_with_no_auth_check():
    code = "router.get('/api/invoices/:id', (req, res) => {\n  res.json(getInvoice(req.params.id));\n});\n"
    issues = scan_content(code, "routes.js")
    missing = [i for i in issues if i["issue_type"] == "missing_authz_check"]
    assert len(missing) == 1


def test_does_not_flag_express_route_with_auth_middleware():
    code = "router.get('/api/invoices/:id', requireAuth, (req, res) => {\n  res.json(getInvoice(req.params.id));\n});\n"
    issues = scan_content(code, "routes.js")
    assert not any(i["issue_type"] == "missing_authz_check" for i in issues)


def test_flags_spring_mapping_with_no_auth_check():
    code = (
        "@GetMapping(\"/api/accounts/{id}\")\n"
        "public Account getAccount(@PathVariable Long id) {\n"
        "    return accountRepository.findById(id);\n"
        "}\n"
    )
    issues = scan_content(code, "AccountController.java")
    missing = [i for i in issues if i["issue_type"] == "missing_authz_check"]
    assert len(missing) == 1


def test_does_not_flag_spring_mapping_with_preauthorize():
    code = (
        "@PreAuthorize(\"hasRole('ADMIN')\")\n"
        "@GetMapping(\"/api/accounts/{id}\")\n"
        "public Account getAccount(@PathVariable Long id) {\n"
        "    return accountRepository.findById(id);\n"
        "}\n"
    )
    issues = scan_content(code, "AccountController.java")
    assert not any(i["issue_type"] == "missing_authz_check" for i in issues)


def test_non_route_code_is_unaffected():
    code = "def add(a, b):\n    return a + b\n"
    issues = scan_content(code, "math.py")
    assert not any(i["issue_type"] == "missing_authz_check" for i in issues)
