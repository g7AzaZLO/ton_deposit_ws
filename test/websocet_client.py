import asyncio
import websockets
import json


async def listen_for_transactions(account_id: str):
    uri = f"ws://127.0.0.1:8000/ws/{account_id}"
    async with websockets.connect(uri) as websocket:
        print(f"Connected to websocket for account: {account_id}")

        try:
            while True:
                message = await websocket.recv()
                transaction = json.loads(message)
                from_address = transaction.get("from_address")
                amount = transaction.get("amount")
                print(f"New transaction received from {from_address}: {amount}")
        except websockets.ConnectionClosed:
            print("Connection closed")


def remain():
    account_id = "0QDgiIGgPiXgqIGxmMFNCqsjdfjS_B1xVINzsOouvmudiDir"
    asyncio.run(listen_for_transactions(account_id))
remain()