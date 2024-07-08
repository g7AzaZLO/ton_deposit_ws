import asyncio
import requests
from fastapi import APIRouter, WebSocket
from settings.ws_deposit_setting import BASE_URL, POLLING_INTERVAL
from typing import List, Dict, Any
from pytoniq_core import Address

ws_deposit_router = APIRouter()


# TODO: сделать чтобы поинты могли быть float

@ws_deposit_router.websocket("/ws/{account_id}")
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
                        print(f"Processing transaction: {tx}")
                        from_address = tx['in_msg']['source']['address']
                        amount = tx['in_msg']['value'] / 1e9
                        user_friendly_address = convert_to_user_friendly(from_address)
                        print(f"Sending transaction from {user_friendly_address} with amount {amount}")
                        await websocket.send_json({"from_address": user_friendly_address, "amount": amount})

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


def convert_to_user_friendly(address: str) -> str:
    """
    Конвертирует адрес в user-friendly формат.

    :param address: Адрес для конвертации.
    :return: Конвертированный адрес.
    """
    addr = Address(address)
    return addr.to_str(is_user_friendly=True, is_bounceable=False, is_url_safe=True, is_test_only=True)
