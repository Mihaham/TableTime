from pydantic import BaseModel
import base64

class InputItem(BaseModel):
    user_id: int


class GameCreate(InputItem):
    game : str

class GameResponse(BaseModel):
    id: int

    class Config:
        orm_mode = True

class GameState(BaseModel):
    image : base64
    text : str


