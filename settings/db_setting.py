import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

DB_URI = os.getenv("DB_URI")

DATABASE_NAME = "Goichev_game"
client = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
db = client[DATABASE_NAME]
users_collection = db['users']
