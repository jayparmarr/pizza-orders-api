import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_order(client, name="Asha", items=None, created_at=None):
    body = {
        "customer_name": name,
        "items": items or [{"pizza": "Margherita", "quantity": 2, "unit_price": 10}],
    }
    if created_at:
        body["created_at"] = created_at
    return client.post("/orders", json=body)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_order_computes_total(client):
    response = make_order(
        client,
        items=[
            {"pizza": "Margherita", "quantity": 2, "unit_price": 10},
            {"pizza": "Farmhouse", "quantity": 1, "unit_price": 12.5},
        ],
    )
    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 32.5
    assert len(body["items"]) == 2


def test_blank_name_is_rejected(client):
    assert make_order(client, name="   ").status_code == 422


def test_zero_quantity_is_rejected(client):
    items = [{"pizza": "Margherita", "quantity": 0, "unit_price": 10}]
    assert make_order(client, items=items).status_code == 422


def test_negative_price_is_rejected(client):
    items = [{"pizza": "Margherita", "quantity": 1, "unit_price": -5}]
    assert make_order(client, items=items).status_code == 422


def test_empty_items_are_rejected(client):
    response = client.post("/orders", json={"customer_name": "Asha", "items": []})
    assert response.status_code == 422


def test_get_missing_order_returns_404(client):
    assert client.get("/orders/999").status_code == 404


def test_list_orders_supports_paging(client):
    for name in ("A", "B", "C"):
        make_order(client, name=name)
    page = client.get("/orders", params={"skip": 1, "limit": 1}).json()
    assert [o["customer_name"] for o in page] == ["B"]


def test_list_limit_is_capped(client):
    assert client.get("/orders", params={"limit": 1000}).status_code == 422


def test_delete_order(client):
    order_id = make_order(client).json()["id"]
    assert client.delete(f"/orders/{order_id}").status_code == 204
    assert client.get(f"/orders/{order_id}").status_code == 404
    assert client.delete(f"/orders/{order_id}").status_code == 404


def test_summary_on_empty_database(client):
    assert client.get("/analytics/summary").json() == {
        "order_count": 0,
        "total_revenue": 0.0,
        "average_order_value": 0.0,
    }


def test_summary_with_orders(client):
    make_order(client, items=[{"pizza": "Margherita", "quantity": 2, "unit_price": 10}])
    make_order(client, items=[{"pizza": "Farmhouse", "quantity": 1, "unit_price": 5}])
    assert client.get("/analytics/summary").json() == {
        "order_count": 2,
        "total_revenue": 25.0,
        "average_order_value": 12.5,
    }


def test_peak_hours_are_ranked(client):
    make_order(client, created_at="2026-01-01T19:15:00")
    make_order(client, created_at="2026-01-02T19:45:00")
    make_order(client, created_at="2026-01-03T12:00:00")
    assert client.get("/analytics/peak-hours").json() == [
        {"hour": 19, "orders": 2},
        {"hour": 12, "orders": 1},
    ]
