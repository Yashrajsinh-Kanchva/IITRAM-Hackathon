def test_protected_page_redirects_when_unauthenticated(client):
    response = client.get("/admin/dashboard", follow_redirects=False)

    assert response.status_code in {301, 302}
    assert "/admin/login" in response.headers["Location"]


def test_admin_login_grants_access(client, admin_credentials):
    login_response = client.post(
        "/admin/login",
        data={
            "email": admin_credentials["email"],
            "password": admin_credentials["password"],
        },
        follow_redirects=False,
    )

    assert login_response.status_code in {302, 303}

    dashboard_response = client.get("/admin/dashboard")
    assert dashboard_response.status_code == 200


def test_user_suspend_updates_status_and_logs_activity(logged_in_client, db):
    user = db.users.find_one({"email": "buyer1@example.com"})

    response = logged_in_client.patch(
        f"/admin/api/users/{user['_id']}/status",
        json={"status": "suspended"},
    )

    assert response.status_code == 200
    updated = db.users.find_one({"_id": user["_id"]})
    assert updated["status"] == "suspended"

    log = db.admin_activity_logs.find_one(
        {"action": "user_status_updated", "entity_id": str(user["_id"])}
    )
    assert log is not None


def test_product_review_updates_status_and_timestamp(logged_in_client, db):
    product = db.products.find_one({"name": "Wheat"})

    response = logged_in_client.patch(
        f"/admin/api/products/{product['_id']}/review",
        json={"status": "approved", "review_note": "Looks good"},
    )

    assert response.status_code == 200
    updated = db.products.find_one({"_id": product["_id"]})
    assert updated["status"] == "approved"
    assert updated["reviewed_at"] is not None


def test_transaction_update_reflects_in_dashboard_kpis(logged_in_client, db):
    transaction = db.transactions.find_one({"transaction_ref": "TXN-1001"})

    update_response = logged_in_client.patch(
        f"/admin/api/transactions/{transaction['_id']}/state",
        json={"payment_status": "failed", "review_state": "flagged"},
    )
    assert update_response.status_code == 200

    kpi_response = logged_in_client.get("/admin/api/dashboard/kpis")
    payload = kpi_response.get_json()

    assert kpi_response.status_code == 200
    assert payload["kpis"]["failed_transactions"] >= 1


def test_api_filters_return_expected_subset(logged_in_client):
    users_response = logged_in_client.get("/admin/api/users?role=farmer")
    users_payload = users_response.get_json()

    assert users_response.status_code == 200
    assert len(users_payload["items"]) == 1
    assert users_payload["items"][0]["role"] == "farmer"

    products_response = logged_in_client.get("/admin/api/products?status=approved")
    products_payload = products_response.get_json()

    assert products_response.status_code == 200
    assert all(item["status"] == "approved" for item in products_payload["items"])
