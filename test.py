from flask import Flask
import chess
import chess.engine
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
stockfish_path = os.path.join(BASE_DIR, "Stockfish", "src", "stockfish")

@app.route("/")
def home():
    board = chess.Board()

    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

    engine.configure({
        "Hash": 16,
        "Threads": 1,
    })

    info = engine.analyse(board, chess.engine.Limit(time=0.1))

    engine.quit()

    return str(info["score"])