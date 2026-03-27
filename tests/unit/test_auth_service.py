from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.admin_user_repository import AdminUserRepository
from app.services.activity_log_service import ActivityLogService
from app.services.auth_service import AuthService


def build_service(db):
    activity = ActivityLogService(ActivityLogRepository(db))
    return AuthService(AdminUserRepository(db), activity)


def test_authenticate_success_updates_last_login(db):
    service = build_service(db)
    admin, error = service.authenticate("admin@example.com", "adminpass123")

    assert error is None
    assert admin is not None
    updated = db.admin_users.find_one({"email": "admin@example.com"})
    assert updated["last_login_at"] is not None


def test_authenticate_rejects_invalid_password(db):
    service = build_service(db)
    admin, error = service.authenticate("admin@example.com", "wrong-password")

    assert admin is None
    assert error == "Invalid email or password"


def test_authenticate_rejects_inactive_admin(db):
    db.admin_users.update_one({"email": "admin@example.com"}, {"$set": {"status": "inactive"}})
    service = build_service(db)

    admin, error = service.authenticate("admin@example.com", "adminpass123")

    assert admin is None
    assert error == "Admin account is not active"
