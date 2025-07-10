from gameengine.app.models import GameResponse
import random

class User():
    def __init__(self, user_id : int):
        self.id = user_id

    def get_id(self):
        return self.id

class Game():
    id = 0
    def __init__(self, name : str, main_user : User):
        self.name = name
        self.main_user = main_user
        self.id = Game.id
        self.users = [main_user]
        Game.id += 1
        self.invite_code = self.generate_invite_code()

        self.is_started = False
        self.status = "Waiting for users"

    def generate_invite_code(self):
        return random.randint(100000, 999999)

    def get_invite_code(self):
        return self.invite_code

    def add_user(self, user : User):
        self.users.append(user)

    def delete_user(self, user : User):
        for old_user in self.users:
            if old_user.get_id() == user.get_id():
                self.users.remove(old_user)


    def start(self):
        self.is_started = True

    def get_status(self):
        return self.status





class GamesEngine():
    pass

