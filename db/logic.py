import logging
from typing import Optional, Dict, Any

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from settings.db_setting import db, users_collection


class Database:
    client: AsyncIOMotorClient = None
    db = None


database = Database()


async def initialize_db() -> None:
    """
    Инициализирует коллекцию пользователей в MongoDB.
    Создает индексы для уникальности и быстрого доступа к полям, таким как userId.
    Если база данных уже существует, выводит соответствующее сообщение.
    """
    try:
        logging.info("Connecting to MongoDB...")
        # Проверка и создание коллекции, если она не существует
        if "users" not in await db.list_collection_names():
            logging.info("Creating collection: users")
            await db.create_collection("users")

        # Получение коллекции пользователей
        existing_indexes = await users_collection.index_information()
        if 'userId_1' in existing_indexes:
            logging.info("Database already initialized with required indexes.")
        else:
            await users_collection.create_index(
                [("ref", "text")], name="search_index", default_language="english"
            )
            await users_collection.create_index("user_id", unique=True)
            logging.info("Database initialized successfully with indexes on user_id")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")


async def close_mongo_connection():
    logging.info("Closing MongoDB connection...")
    database.client.close()
    logging.info("MongoDB connection closed")


def user_helper(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Формирует словарь с информацией о пользователе из документа MongoDB.

    :param user: Документ MongoDB с данными пользователя.
    :return: Словарь с данными пользователя.
    """
    return {
        "id": str(user["_id"]),
        "user_id": user["user_id"],
        "username": user["username"],
        "wallet": user["wallet"],
        "points": user["points"],
    }


async def retrieve_user(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Извлекает пользователя по user_id из базы данных.

    :param user_id: Идентификатор пользователя для поиска.
    :return: Словарь с данными пользователя или None, если пользователь не найден.
    """
    user = await db["users"].find_one({"user_id": user_id})
    if user:
        return user_helper(user)
    return None


async def add_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Добавляет нового пользователя в базу данных.

    :param user_data: Словарь с данными пользователя.
    :return: Словарь с данными добавленного пользователя.
    """
    user = await db["users"].insert_one(user_data)
    new_user = await db["users"].find_one({"_id": user.inserted_id})
    return user_helper(new_user)


async def update_user(user_id: int, data: Dict[str, Any]) -> bool:
    """
    Обновляет данные пользователя по user_id.

    :param user_id: Идентификатор пользователя для обновления.
    :param data: Словарь с обновленными данными пользователя.
    :return: True, если обновление было успешным, иначе False.
    """
    if len(data) < 1:
        return False
    user = await db["users"].find_one({"user_id": user_id})
    if user:
        updated_user = await db["users"].update_one(
            {"user_id": user_id}, {"$set": data}
        )
        if updated_user.modified_count > 0:
            return True
    return False


async def update_wallet(user_id: int, new_wallet: str) -> Optional[Dict[str, Any]]:
    """
    Обновляет кошелек пользователя по user_id.

    :param user_id: Идентификатор пользователя.
    :param new_wallet: Новый кошелек для пользователя.
    :return: Словарь с обновленными данными пользователя или None, если пользователь не найден или кошелек уже существует.
    """
    existing_wallet = await db["users"].find_one({"wallet": new_wallet})
    if existing_wallet:
        raise HTTPException(status_code=400, detail="Wallet already exists")

    user = await db["users"].find_one({"user_id": user_id})
    if user:
        updated_user = await db["users"].update_one(
            {"user_id": user_id}, {"$set": {"wallet": new_wallet}}
        )
        if updated_user.modified_count > 0:
            return await retrieve_user(user_id)
    return None


async def add_points(user_id: int, amount: int) -> Optional[Dict[str, Any]]:
    """
    Добавляет количество очков к пользователю по user_id.

    :param user_id: Идентификатор пользователя для обновления.
    :param amount: Количество очков для начисления.
    :return: Словарь с обновленными данными пользователя или None, если пользователь не найден.
    """
    user = await db["users"].find_one({"user_id": user_id})
    if user:
        new_points = user["points"] + amount
        updated_user = await db["users"].update_one(
            {"user_id": user_id}, {"$set": {"points": new_points}}
        )
        if updated_user.modified_count > 0:
            return await retrieve_user(user_id)
    return None


async def subtract_points(user_id: int, amount: int) -> Optional[Dict[str, Any]]:
    """
    Уменьшает количество очков у пользователя по user_id.

    :param user_id: Идентификатор пользователя для обновления.
    :param amount: Количество очков для вычитания.
    :return: Словарь с обновленными данными пользователя или None, если пользователь не найден.
    """
    user = await db["users"].find_one({"user_id": user_id})
    if user:
        new_points = user["points"] - amount
        if new_points < 0:
            new_points = 0  # Убедимся, что количество очков не может быть отрицательным
        updated_user = await db["users"].update_one(
            {"user_id": user_id}, {"$set": {"points": new_points}}
        )
        if updated_user.modified_count > 0:
            return await retrieve_user(user_id)
    return None


async def delete_user(user_id: int) -> bool:
    """
    Удаляет пользователя по user_id.

    :param user_id: Идентификатор пользователя для удаления.
    :return: True, если удаление было успешным, иначе False.
    """
    user = await db["users"].find_one({"user_id": user_id})
    if user:
        await db["users"].delete_one({"user_id": user_id})
        return True
    return False


async def transfer_points_by_user_id(from_user_id: int, to_user_id: int, amount: int) -> Optional[Dict[str, Any]]:
    """
    Переводит очки от одного пользователя к другому по их user_id.

    :param from_user_id: Идентификатор отправителя.
    :param to_user_id: Идентификатор получателя.
    :param amount: Количество очков для перевода.
    :return: Словарь с обновленными данными обоих пользователей или None, если перевод не удался.
    """
    from_user = await db["users"].find_one({"user_id": from_user_id})
    to_user = await db["users"].find_one({"user_id": to_user_id})
    if from_user and to_user:
        if from_user["points"] >= amount:
            new_from_user_points = from_user["points"] - amount
            new_to_user_points = to_user["points"] + amount
            await db["users"].update_one({"user_id": from_user_id}, {"$set": {"points": new_from_user_points}})
            await db["users"].update_one({"user_id": to_user_id}, {"$set": {"points": new_to_user_points}})
            return {
                "from_user": await retrieve_user(from_user_id),
                "to_user": await retrieve_user(to_user_id)
            }
    return None


async def transfer_points_by_wallet(from_wallet: str, to_wallet: str, amount: int) -> Optional[Dict[str, Any]]:
    """
    Переводит очки от одного пользователя к другому по их wallet.

    :param from_wallet: Кошелек отправителя.
    :param to_wallet: Кошелек получателя.
    :param amount: Количество очков для перевода.
    :return: Словарь с обновленными данными обоих пользователей или None, если перевод не удался.
    """
    from_user = await db["users"].find_one({"wallet": from_wallet})
    to_user = await db["users"].find_one({"wallet": to_wallet})
    if from_user and to_user:
        if from_user["points"] >= amount:
            new_from_user_points = from_user["points"] - amount
            new_to_user_points = to_user["points"] + amount
            await db["users"].update_one({"wallet": from_wallet}, {"$set": {"points": new_from_user_points}})
            await db["users"].update_one({"wallet": to_wallet}, {"$set": {"points": new_to_user_points}})
            return {
                "from_user": await retrieve_user(from_user["user_id"]),
                "to_user": await retrieve_user(to_user["user_id"])
            }
    return None


async def retrieve_user_by_wallet(wallet: str) -> Optional[Dict[str, Any]]:
    """
    Извлекает пользователя по кошельку из базы данных.

    :param wallet: Кошелек пользователя для поиска.
    :return: Словарь с данными пользователя или None, если пользователь не найден.
    """
    return await db["users"].find_one({"wallet": wallet})
