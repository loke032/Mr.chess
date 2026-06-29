import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, 'data/games.json')

with open(FILE_PATH, 'r') as f:
    saved_data = json.load(f)
    

games = saved_data['games']

new_games = {}
for game_name, fen_list in games.items():
    if isinstance(fen_list, dict):
        new_games[game_name] = fen_list
        continue

    new_games[game_name] = {'fens': fen_list, 'orientation': 'white'}

saved_data['games'] = new_games


with open(FILE_PATH, 'w') as f:
    json.dump(saved_data, f, indent=4)

print("Games converted successfully!")