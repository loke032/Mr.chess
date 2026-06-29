import csv
import json
import os
import chess
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, 'data/puzzles.json')
puzzles = []

with open('lichess_db_puzzle.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)

    for i, row in enumerate(reader):
        puzzle = {
            'fen': row['FEN'],
            'moves': row['Moves'].split()
        }
        puzzles.append(puzzle)

        if i >= 9000:
            break

    clean_puzzles = []

    for p in puzzles:
        board = chess.Board(p['fen'])

        board.push_uci(p['moves'][0])

        clean_puzzles.append({
            'fen': board.fen(),
            'moves': p['moves'][1:]
        })
with open(FILE_PATH, 'w') as file:
    json.dump(clean_puzzles, file, indent=4)