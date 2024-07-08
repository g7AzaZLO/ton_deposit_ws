from pydantic import BaseModel, Field


class User(BaseModel):
    user_id: int = Field(ge=0)
    username: str
    wallet: str
    points: int = Field(ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 632452342,
                "username": "john_doe",
                "wallet": "BE_irfow539Vdocjif434_vdjo-vxodijVBXdkiv",
                "points": 0
            }
        }
