from werkzeug.security import check_password_hash


class AuthService:
    def __init__(self, admin_repo, activity_log_service):
        self.admin_repo = admin_repo
        self.activity_log_service = activity_log_service

    def authenticate(self, email, password):
        admin = self.admin_repo.find_by_email(email)
        if not admin:
            return None, "Invalid email or password"

        if admin.get("status") != "active":
            return None, "Admin account is not active"

        if not check_password_hash(admin.get("password_hash", ""), password):
            return None, "Invalid email or password"

        self.admin_repo.update_last_login(admin["_id"])
        self.activity_log_service.log(
            admin["_id"],
            action="admin_login",
            entity_type="admin_user",
            entity_id=admin["_id"],
            details={"email": admin.get("email")},
        )
        return admin, None

    def get_public_admin(self, admin_id):
        admin = self.admin_repo.find_by_id(admin_id)
        return self.admin_repo.to_public(admin)
