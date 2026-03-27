from datetime import timedelta

from app.utils.time_utils import utcnow


def test_analytics_3d_route_returns_200_and_valid_structure(logged_in_client, db):
    now = utcnow()
    db.orders.insert_many(
        [
            {
                "order_number": "ORD-3D-INT-1",
                "status": "confirmed",
                "total_amount": 2100,
                "quantity": 8,
                "created_at": now - timedelta(hours=2),
                "updated_at": now - timedelta(hours=2),
            },
            {
                "order_number": "ORD-3D-INT-2",
                "status": "packed",
                "total_amount": 1100,
                "quantity": 2,
                "created_at": now - timedelta(hours=1),
                "updated_at": now - timedelta(hours=1),
            },
        ]
    )

    response = logged_in_client.get("/admin/api/analytics/3d-data?range=30d")
    assert response.status_code == 200

    payload = response.get_json()
    assert isinstance(payload, list)
    if payload:
        sample = payload[0]
        assert "time" in sample
        assert "price" in sample
        assert "quantity" in sample


def test_analytics_3d_route_blocks_unauthorized(client):
    response = client.get("/admin/api/analytics/3d-data?range=30d")
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data


def test_analytics_3d_route_returns_400_for_invalid_range(logged_in_client):
    response = logged_in_client.get("/admin/api/analytics/3d-data?range=365d")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
