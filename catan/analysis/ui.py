import requests
import webbrowser


SERVER_URL = "http://localhost:6969/api/games"
UI_URL = "http://localhost:3000"


def create_game(players) -> str:
    payload = {"players": players}
    response = requests.post(SERVER_URL, json=payload).json()
    return response["game_id"]


def view_game(game_id):
    webbrowser.open(f"{UI_URL}/games/{game_id}")
