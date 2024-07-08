from fastapi import APIRouter, HTTPException
from db.model import User
from db.logic import (
    retrieve_user,
    add_user,
    update_user,
    delete_user, add_points, subtract_points, transfer_points_by_user_id, transfer_points_by_wallet, update_wallet,
    retrieve_user_by_wallet,
)

db_router = APIRouter()


@db_router.post("/users/", response_model=User, tags=["Users"])
async def create_user(user: User) -> User:
    """
    Создает нового пользователя.

    :param user: Объект User, содержащий данные пользователя.
    :return: Словарь с данными нового пользователя.
    """
    user_data = user.dict()
    new_user = await add_user(user_data)
    return new_user


@db_router.get("/users/{user_id}", response_model=User, tags=["Users"])
async def read_user(user_id: int) -> User:
    """
    Извлекает пользователя по user_id.

    :param user_id: Идентификатор пользователя для поиска.
    :return: Словарь с данными пользователя.
    :raises HTTPException: Если пользователь не найден.
    """
    user = await retrieve_user(user_id)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


@db_router.put("/users/{user_id}", response_model=User, tags=["Users"])
async def update_user_info(user_id: int, user: User) -> User:
    """
    Обновляет данные пользователя по user_id.

    :param user_id: Идентификатор пользователя для обновления.
    :param user: Объект User с обновленными данными пользователя.
    :return: Словарь с обновленными данными пользователя.
    :raises HTTPException: Если пользователь не найден.
    """
    update_data = user.dict()
    updated_user = await update_user(user_id, update_data)
    if updated_user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


@db_router.put("/users/{user_id}/add_points", response_model=User, tags=["Users"])
async def add_points_for_user(user_id: int, amount: int) -> User:
    """
    Обновляет количество очков пользователя по user_id.

    :param user_id: Идентификатор пользователя для обновления.
    :param amount: Количество очков для начисления.
    :return: Словарь с обновленными данными пользователя.
    :raises HTTPException: Если пользователь не найден.
    """
    updated_user = await add_points(user_id, amount)
    if updated_user:
        return updated_user
    raise HTTPException(status_code=404, detail="User not found")


@db_router.put("/users/{user_id}/subtract_points", response_model=User, tags=["Users"])
async def subtract_points_for_user(user_id: int, amount: int) -> User:
    """
    Уменьшает количество очков пользователя по user_id.

    :param user_id: Идентификатор пользователя для обновления.
    :param amount: Количество очков для вычитания.
    :return: Словарь с обновленными данными пользователя.
    :raises HTTPException: Если пользователь не найден.
    """
    updated_user = await subtract_points(user_id, amount)
    if updated_user:
        return updated_user
    raise HTTPException(status_code=404, detail="User not found")


@db_router.put("/users/{user_id}/update_wallet", response_model=User, tags=["Users"])
async def update_user_wallet(user_id: int, new_wallet: str) -> User:
    """
    Обновляет кошелек пользователя по user_id.

    :param user_id: Идентификатор пользователя.
    :param new_wallet: Новый кошелек для пользователя.
    :return: Обновленные данные пользователя.
    :raises HTTPException: Если пользователь не найден или кошелек уже существует.
    """
    updated_user = await update_wallet(user_id, new_wallet)
    if updated_user:
        return updated_user
    raise HTTPException(status_code=404, detail="User not found or wallet already exists")


@db_router.delete("/users/{user_id}", tags=["Users"])
async def delete_user(user_id: int) -> dict:
    """
    Удаляет пользователя по user_id.

    :param user_id: Идентификатор пользователя для удаления.
    :return: Сообщение об успешном удалении пользователя.
    :raises HTTPException: Если пользователь не найден.
    """
    deleted_user = await delete_user(user_id)
    if deleted_user:
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")


@db_router.get("/users/by_wallet/{wallet}", response_model=User, tags=["Users"])
async def get_user_by_wallet(wallet: str):
    user = await retrieve_user_by_wallet(wallet)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


@db_router.put("/transfer/transfer_points_by_user_id", response_model=User, tags=["Transfers"])
async def transfer_points_user_id(from_user_id: int, to_user_id: int, amount: int):
    """
    Переводит очки от одного пользователя к другому по их user_id.

    :param from_user_id: Идентификатор отправителя.
    :param to_user_id: Идентификатор получателя.
    :param amount: Количество очков для перевода.
    :raises HTTPException: Если один из пользователей не найден или недостаточно очков у отправителя.
    """
    if from_user_id == to_user_id:
        raise HTTPException(status_code=400, detail="Cannot transfer points to the same user.")

    updated_users = await transfer_points_by_user_id(from_user_id, to_user_id, amount)
    if updated_users:
        return updated_users
    raise HTTPException(status_code=404, detail="Transfer failed. Check user IDs and points balance.")


@db_router.put("/transfer/transfer_points_by_wallet", response_model=User, tags=["Transfers"])
async def transfer_points_wallet(from_wallet: str, to_wallet: str, amount: int):
    """
    Переводит очки от одного пользователя к другому по их wallet.

    :param from_wallet: Кошелек отправителя.
    :param to_wallet: Кошелек получателя.
    :param amount: Количество очков для перевода.
    :raises HTTPException: Если один из пользователей не найден или недостаточно очков у отправителя.
    """
    if from_wallet == to_wallet:
        raise HTTPException(status_code=400, detail="Cannot transfer points to the same user.")

    updated_users = await transfer_points_by_wallet(from_wallet, to_wallet, amount)
    if updated_users:
        return updated_users
    raise HTTPException(status_code=404, detail="Transfer failed. Check wallet addresses and points balance.")
