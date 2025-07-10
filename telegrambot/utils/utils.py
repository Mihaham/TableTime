import requests


def is_admin(user_id):
    return False #Пока не реализован database_interface


def create_game(user_id, name):
    payload = {"user_id" : user_id, "name" : name}
    response = requests.post("", json = payload)
    if response.status_code != 200:
        pass
    return response.json()["invite_code"]

def join_game(user_id, invite_code):
    payload = {"user_id" : user_id, "invite_code" : invite_code}
    response = requests.post("", json = payload)
    if response.status_code == 404:
        raise ValueError("Invite code does not exist")
    elif response.status_code == 406:
        raise ValueError("You are already joined")


