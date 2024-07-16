from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import random
import asyncio
import uuid
from typing import Dict, List

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>XM AI Live Trading platform</h1>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
        </script>
    </body>
</html>
"""


class Order(BaseModel):
    """
    Model representing an order.
    :param: id (str): The unique identifier of the order.
    :param: status (str): The current status of the order.
    """
    id: str
    status: str


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    :param: active_connections (Dict[str, WebSocket]): Dictionary to hold active WebSocket connections.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Connects a WebSocket client.
        :param: websocket (WebSocket): The WebSocket connection.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Disconnects a WebSocket client.
        :param: websocket (WebSocket): The WebSocket connection.
        """
        self.active_connections.remove(websocket)

    async def send_update(self, order: Order):
        """
        Sends order status updates to all connected clients.
        :param: order (Order): The order object with updated status.
        """
        for connection in self.active_connections:
            await connection.send_json({"orderId": order.id, "status": order.status})


# In-memory database to store orders
orders: Dict[str, Order] = {}
# Instantiate the connection manager
manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.post("/orders", response_model=Order)
async def create_order(execute_order: bool = True) -> Order:
    """
    Creates a new order with PENDING status.
    :return: Order: The created order object.
    """
    # Generate a unique order ID
    order_id = str(uuid.uuid4())
    # Create a new order with PENDING status
    order = Order(id=order_id, status="PENDING")
    # Store the order in the in-memory database
    orders[order_id] = order
    # Schedule the order status update to EXECUTED
    await manager.send_update(order)
    if execute_order:
        await asyncio.create_task(update_order_status(order_id))
    return order


@app.get("/orders", response_model=List[Order])
async def get_order() -> List[Order]:
    """
    Fetches the details of an order by its ID.
    :param: order_id (str): The unique identifier of the order.
    :return: Order: The order object.
    :raise: HTTPException: If the order is not found.
    """
    if not orders:
        raise HTTPException(status_code=404, detail="Orders are empty")
    return list(orders.values())


@app.get("/orders/{order_id}", response_model=Order)
async def get_orders(order_id: str) -> Order:
    """
    Fetches the details of an order by its ID.
    :param: order_id (str): The unique identifier of the order.
    :return: Order: The order object.
    :raise: HTTPException: If the order is not found.
    """
    if order_id not in orders:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return orders[order_id]


@app.delete("/orders/{order_id}")
async def delete_order(order_id: str) -> Dict[str, str]:
    """
    Cancels a PENDING order by its ID.
    :param: order_id (str): The unique identifier of the order.
    :return: dict: A message indicating the order has been cancelled.
    :raise: HTTPException: If the order is not found or cannot be cancelled.
    """
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    if orders[order_id].status != "PENDING":
        raise HTTPException(status_code=400, detail="Cannot cancel non-pending order")
    orders[order_id].status = "CANCELLED"
    await manager.send_update(orders[order_id])
    del orders[order_id]
    return {"detail": "Order cancelled"}


async def update_order_status(order_id: str):
    """
    Updates the order status to EXECUTED after a random delay.
    :param: order_id (str): The unique identifier of the order.
    """
    # await manager.send_update(orders[order_id])
    await asyncio.sleep(random.uniform(0.1, 1))
    if order_id in orders:
        orders[order_id].status = "EXECUTED"
        await manager.send_update(orders[order_id])


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Handles WebSocket connections for real-time order updates.
    :param: websocket (WebSocket): The WebSocket connection.
    """
    # Connect the WebSocket client
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Disconnect the client on WebSocket disconnection
        manager.disconnect(websocket)
