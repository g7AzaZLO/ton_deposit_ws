import asyncio
import websockets
import json
import logging
import requests
import httpx

logging.basicConfig(level=logging.INFO)

WEBSOCKET_URL = "ws://127.0.0.1:8000/ws/{account_id}"  # URL WebSocket сервера
ACCOUNT_ID = "0QDgiIGgPiXgqIGxmMFNCqsjdfjS_B1xVINzsOouvmudiDir"  # Укажите здесь идентификатор вашего аккаунта
API_BASE_URL = "http://127.0.0.1:8000"


async def process_transaction(transaction: dict):
    from_address = transaction["from_address"]
    amount = transaction["amount"]

    user = await retrieve_user_by_wallet(from_address)
    if user:
        response = await add_points(user["user_id"], amount)
        if response.status_code == 200:
            logging.info(f"Added {amount*100} points to user with wallet {from_address}") ### тут коэфф любй
        else:
            logging.error(f"Failed to add points: {response.text}")
    else:
        logging.warning(f"Wallet {from_address} not found in the database")


async def websocket_handler():
    uri = WEBSOCKET_URL.format(account_id=ACCOUNT_ID)
    async with websockets.connect(uri) as websocket:
        logging.info(f"Connected to WebSocket server at {uri}")
        while True:
            message = await websocket.recv()
            logging.debug(f"Received message: {message}")
            transaction = json.loads(message)
            await process_transaction(transaction)


async def retrieve_user_by_wallet(wallet: str):
    """
    Извлекает пользователя по кошельку из базы данных через API.

    :param wallet: Кошелек пользователя для поиска.
    :return: Словарь с данными пользователя или None, если пользователь не найден.
    """
    url = f"{API_BASE_URL}/users/by_wallet/{wallet}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()
    return None


async def add_points(user_id: int, amount: int):
    """
    Добавляет поинты пользователю через API.

    :param user_id: Идентификатор пользователя.
    :param amount: Количество поинтов для добавления.
    :return: Ответ от API.
    """
    url = f"{API_BASE_URL}/users/{user_id}/add_points?amount={amount*100}" ### тут коэфф любой
    async with httpx.AsyncClient() as client:
        response = await client.put(url)
        return response


if __name__ == "__main__":
    try:
        asyncio.run(websocket_handler())
    except KeyboardInterrupt:
        logging.info("WebSocket client stopped")
