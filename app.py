import time
from typing import List, Dict, Any
import requests
import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="[G7]NewDepositWS"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://testnet.tonapi.io/v2/blockchain/accounts"
POLLING_INTERVAL = 10  # Интервал опроса в секундах


@app.websocket("/ws/{account_id}")
async def websocket_endpoint(websocket: WebSocket, account_id: str):
    await websocket.accept()
    last_transaction_id = None
    print(f"WebSocket connection established for account: {account_id}")

    # Initial fetch to set the last_transaction_id without sending old transactions
    transactions = fetch_transactions(account_id)
    if transactions:
        last_transaction_id = transactions[0]["hash"]

    while True:
        try:
            transactions = fetch_transactions(account_id)
            print(f"Fetched transactions: {transactions}")  # Debugging output
            new_transactions = get_new_transactions(transactions, last_transaction_id)

            if new_transactions:
                for tx in new_transactions:
                    if tx['success']:
                        print(f"Processing transaction: {tx}")  # Debugging output
                        from_address = tx['in_msg']['source']['address']
                        amount = tx['in_msg']['value'] / 1e9
                        print(f"Sending transaction from {from_address} with amount {amount}")  # Debugging output
                        await websocket.send_json({"from_address": from_address, "amount": amount})

                # Обновляем идентификатор последней транзакции только если были новые транзакции
                last_transaction_id = new_transactions[0]["hash"]

            await asyncio.sleep(POLLING_INTERVAL)
        except Exception as e:
            print(f"Error: {e}")  # Debugging output


def fetch_transactions(account_id: str) -> List[Dict[str, Any]]:
    url = f"{BASE_URL}/{account_id}/transactions"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["transactions"]


def get_new_transactions(transactions: List[Dict[str, Any]], last_transaction_id: str) -> List[Dict[str, Any]]:
    new_transactions = []

    # Найти первую новую транзакцию после last_transaction_id
    for tx in transactions:
        if tx["hash"] == last_transaction_id:
            break
        new_transactions.append(tx)

    return new_transactions


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
