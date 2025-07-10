class AccessError(ValueError):
    pass

class GameAmountError(ValueError):
    pass

NotHostError = ValueError("User is not host")
IsNotConnectedError = ValueError("Пользователь не присоединен ни к одной игре")