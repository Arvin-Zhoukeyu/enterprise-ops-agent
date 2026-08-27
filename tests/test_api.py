from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root():

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert (
        data["service"]
        == "EnterpriseOps Agent"
    )


def test_health():

    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_list_suppliers():

    response = client.get(
        "/api/v1/suppliers?limit=5"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data,
        list,
    )

    assert len(data) <= 5


def test_high_risk_supplier_filter():

    response = client.get(
        "/api/v1/suppliers"
        "?risk_level=high"
        "&limit=20"
    )

    assert response.status_code == 200

    data = response.json()

    for supplier in data:

        assert (
            supplier["risk_level"]
            == "high"
        )


def test_list_orders():

    response = client.get(
        "/api/v1/orders?limit=5"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data,
        list,
    )


def test_high_risk_orders_endpoint():

    response = client.get(
        "/api/v1/orders/high-risk"
        "?days=365"
        "&min_amount=50000"
        "&min_delay_days=7"
        "&min_historical_delays=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data,
        list,
    )