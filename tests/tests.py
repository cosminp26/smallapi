import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app, ConnectionManager

client = TestClient(app)


@pytest.fixture
def connection_manager():
    return ConnectionManager()


@pytest.fixture
def create_order():
    response = client.post("/orders")
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def create_order_pending():
    response = client.post("/orders?execute_order=false")
    assert response.status_code == 200
    return response.json()


def test_create_order():
    response = client.post("/orders")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "EXECUTED"


def test_get_order(create_order):
    order_id = create_order["id"]
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id
    assert data["status"] == "EXECUTED"


def test_get_nonexistent_order():
    response = client.get("/orders/nonexistent")
    assert response.status_code == 404


def test_get_orders():
    client.post("/orders")
    client.post("/orders")
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_delete_order(create_order_pending):
    order_id = create_order_pending["id"]
    response = client.delete(f"/orders/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Order cancelled"


def test_delete_executed_order(create_order):
    order_id = create_order["id"]
    response = client.delete(f"/orders/{order_id}")
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Cannot cancel non-pending order"


def test_delete_nonexistent_order():
    response = client.delete("/orders/nonexistent")
    assert response.status_code == 404


def test_websocket():
    messages = []
    with client.websocket_connect("/ws") as websocket:
        order = client.post("/orders")

        # Receive the initial status update
        for _ in range(2):
            message = websocket.receive_json()
            if message["orderId"] == order.json()["id"]:
                messages.append(message)
        assert len(messages) == 2
        assert messages[0]["status"] == "PENDING"
        assert messages[1]["status"] == "EXECUTED"


@pytest.mark.asyncio
async def test_performance():
    with client.websocket_connect("/ws") as websocket:
        execution_times_orders = []
        execution_times_websocket = []

        for _ in range(100):
            response_start = time.time()
            response = client.post("/orders")
            execution_times_orders.append(time.time() - response_start)

            websocket_start = time.time()
            websocket.receive_text()
            execution_times_websocket.append(time.time() - websocket_start)

            assert response.status_code == 200

        diff_execution_time = [a - b for a, b in zip(execution_times_orders, execution_times_websocket)]
        avg_orders_execution_delay = np.mean(diff_execution_time)
        std_deviation = np.std(diff_execution_time)

        print(f"\nAverage Order Execution Delay: {avg_orders_execution_delay:.4f} seconds")
        print(f"Standard Deviation: {std_deviation:.4f} seconds")
