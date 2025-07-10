from pydantic import BaseModel
import base64

class InputItem(BaseModel):
    user_id: int


class GameCreate(InputItem):
    game : str

class GameResponse(BaseModel):
    invite_code: int

class JoinCreate(InputItem):
    invite_code : int

class GameState(BaseModel):
    image : str
    text : str

class UserItem(BaseModel):
    user_id : int


