import random
from app.error.error import AccessError, GameAmountError, IsNotConnectedError, NotHostError

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

    def get_main_user_id(self):
        return self.main_user.get_id()

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

    def get_user_ids(self):
        return [user.get_id() for user in self.users]


    def start(self):
        self.is_started = True

    def get_status(self):
        return self.status


    def check_user(self, user_id):
        for user in self.users:
            if user.get_id() == user_id:
                return True
        return False

    def start(self):
        self.is_started = True




class GamesEngine():
    def __init__(self) -> None:
        self.games = []

    def create_game(self, user_id : int, name : str):
        self.games.append(Game(name, User(user_id)))
        return self.games[-1].get_invite_code()

    def append_game(self, game : Game):
        self.games.append(game)

    def get_game_id(self, user_id):
        self.get_game(user_id).get_id()

    def get_game(self, user_id):
        for game in self.games:
            if user_id in game.get_user_ids():
                return game

    def get_invite_code(self, user_id):
        for game in self.games:
            if user_id in game.get_user_ids():
                return game.get_id()

    def delete_game(self, game : Game):
        self.games.remove(game)

    def delete_game_by_main_user_id(self, user_id: int):
        for game in self.games:
            if game.get_main_user_id() == user_id:
                self.games.remove(game)
                break

    def add_user(self, user_id : int, invite_code : int):
        if self.check_user(user_id):
            raise GameAmountError("Пользователь уже присоединен к другой игре")
        for game in self.games:
            if game.get_invite_code() == invite_code:
                game.add_user(User(user_id))
                return True
        raise ValueError("Invalid Invite Code")

    def remove_user(self, user_id : int):
        for game in self.games:
            if game.check_user(user_id):
                game.remove_user(user_id)
                break
        raise IsNotConnectedError

    def check_user(self, user_id):
        for game in self.games:
            if game.check_user(user_id):
                return True
        return False

    def start_game(self, user_id):
        if not self.check_user(user_id):
            raise IsNotConnectedError
        for game in self.games:
            if game.get_main_user_id() == user_id:
                game.start()
                return game.get_user_ids()
        raise NotHostError

    def get_user_ids(self, user_id):
        return self.get_game(user_id).get_user_ids()

