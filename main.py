import chess
import chess.engine
from flask import Flask, render_template, request, redirect
import os
from flask import json
import random
from threading import Lock
from flask import session
import shutil
import requests
import tarfile
import resource



file_lock = Lock()

app = Flask(__name__)

app.secret_key = "some_long_random_string"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "data/games.json")

BASE_DIR1 = os.path.dirname(os.path.abspath(__file__))
FILE_PATH1 = os.path.join(BASE_DIR, "data/puzzles.json")



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

stockfish_path = os.path.join(
    BASE_DIR,
    "Stockfish",
    "src",
    "stockfish"
)

test_engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)




def get_board():
    with open(FILE_PATH, "r") as f:
        data = json.load(f)
        saved_data = data["users"][session["username"]]
    games = saved_data["games"]
    if not games:
        return chess.Board()
    latest_game = list(games.keys())[-1]
    print("loading:", latest_game)
    fen = games[latest_game]["fens"][-1]
    return chess.Board(fen)


def is_new_game(board):
    with open (FILE_PATH, 'r') as f:
        data = json.load(f)
        saved_data = data["users"][session["username"]]
        local_play = saved_data["local_play"]
    if local_play:
        return board.fen() == chess.STARTING_FEN
    else:
        return board.fen() == chess.STARTING_FEN or (
            board.fullmove_number == 1 and board.turn == chess.BLACK
        )


def get_material(board):

    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
    }

    white_material = 0
    black_material = 0

    for piece_type in piece_values:

        value = piece_values[piece_type]

        white_material += len(board.pieces(piece_type, chess.WHITE)) * value

        black_material += len(board.pieces(piece_type, chess.BLACK)) * value

    return white_material - black_material


def get_bot_move(board):
    print("BOT MOVE FUNCTION STARTED")


    with open(FILE_PATH, "r") as f:
            data = json.load(f)
            saved_data = data["users"][session["username"]]
            difficulty = saved_data["difficulty"]
            bot_time = saved_data["bot_time"]
            print("Bot time:", bot_time)
    print("starting analysis")
    info = test_engine.analyse(board, chess.engine.Limit(time=bot_time), multipv=5)
    print("Finished analysis")

    candidates = []

    for line in info:
        if "pv" in line and "score" in line:
            move = line["pv"][0]
            score = line["score"].relative.score(mate_score=10000)

            candidates.append((move, score))

    if not candidates:
        result = test_engine.play(board, chess.engine.Limit(time=bot_time))
        bot_move = result.move
    else:
        if difficulty == "beginner":
            bot_move = random.choice(candidates)[0]
        elif difficulty == "novice":
            top_moves = candidates[:4]
            weights = [4, 3, 2, 1][: len(top_moves)]
            bot_move = random.choices([m for m, s in top_moves], weights=weights, k=1)[
                0
            ]
        elif difficulty == "intermediate":
            top_moves = candidates[:3]
            weights = [6, 3, 1][: len(top_moves)]
            bot_move = random.choices([m for m, s in top_moves], weights=weights, k=1)[
                0
            ]
        elif difficulty == "advanced":
            top_moves = candidates[:2]
            weights = [9, 1][: len(top_moves)]
            bot_move = random.choices([m for m, s in top_moves], weights=weights, k=1)[
                0
            ]
        elif difficulty == "master":
            bot_move = candidates[0][0]
        else:
            result = test_engine.play(board, chess.engine.Limit(time=bot_time))
            bot_move = result.move
    return bot_move

    


def format_time(time_seconds):
    minutes = time_seconds // 60
    seconds = time_seconds % 60
    return f"{minutes:02}:{seconds:02}"


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        print("signing up")
        username = request.form.get("username")
        password = request.form.get("password")

        with open(FILE_PATH, "r") as f:
            saved_data = json.load(f)

        if username in saved_data["users"]:
            return "Username already exists. Try again."

        saved_data["users"][username] = {
            "password": password,
            "elo": 0,
            "puzzle_streak": 0,
            "games": {},
            "current_puzzle": None,
            "puzzle_index": 0,
            "puzzle_board": None,
            "difficulty": "beginner",
            "bot_time": 0.01,
            "player_color": "white",
            "local_play": False,
            "current_game": None,
            "resigned": False,
            "time": 300,
            "local_play_button_pressed": False,
            "bot_analysis": None,
            "new_game": True,
            "color_setting": "white",
            "auto_skip": False,
            "auto_skip_pressed": False,
            "puzzle_completed": False
        }

        with file_lock:
            with open(FILE_PATH, "w") as f:
                json.dump(saved_data, f, indent=4)
        session["username"] = username

        return redirect("/")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        with open(FILE_PATH, "r") as f:
            saved_data = json.load(f)
        if not username in saved_data["users"]:
            return "Username does not exist. Please try again."
        if saved_data["users"][username]["password"] == password:
            session["username"] = username
        else:
            return "Password does not match. Please try again."
        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/", methods=["GET", "POST"])
def home():
    if "username" not in session:
        return redirect("/signup")
    

    try:
        with open(FILE_PATH, "r") as f:
            data = json.load(f)
            saved_data = data["users"][session["username"]]
            current_puzzle = saved_data["current_puzzle"]
            puzzle_index = saved_data["puzzle_index"]
            difficulty = saved_data["difficulty"]
            bot_time = saved_data["bot_time"]
            player_color = saved_data["player_color"]
            local_play = saved_data["local_play"]
            resigned = saved_data["resigned"]
            time = saved_data["time"]
            local_play_button_pressed = saved_data["local_play_button_pressed"]
            bot_analysis = saved_data["bot_analysis"]
            new_game = saved_data["new_game"]
            color_setting = saved_data["color_setting"]
            auto_skip = saved_data["auto_skip"]
            auto_skip_pressed = saved_data["auto_skip_pressed"]
            puzzle_completed = saved_data["puzzle_completed"]
            current_game = chess.Board(saved_data["current_game"]) if saved_data["current_game"] else None
            puzzle_board = chess.Board(saved_data["puzzle_board"]) if saved_data["puzzle_board"] else None


    except Exception:
        print("could not open the games.json file!(start og home)")
        data = {"users": {}}
        with file_lock:
            with open(FILE_PATH, "w") as f:
                json.dump(data, f, indent=4)

    username = session["username"]
    try:
        white_time = int(time)
        black_time = int(time)
    except Exception:
        white_time = 300
        black_time = 300
    try:
        games = saved_data["games"]
    except Exception:
        return redirect("/login")
    if not games:
        board = current_game if current_game else chess.Board()

        saved_data["current_game"] = board.fen()
        saved_data["new_game"] = True

        with file_lock:
            with open(FILE_PATH, "w") as f:
                json.dump(data, f, indent=4)
        
        return render_template(
            "home.html",
            fen=board.fen(),
            white_turn=board.turn,
            local_play=local_play,
            white_time=white_time,
            black_time=black_time,
            message="",
            resigned=resigned,
            clock_started=False,
            clean_white_time=format_time(white_time),
            clean_black_time=format_time(black_time),
            elo=saved_data["elo"],
            username=username,
            difficulty=difficulty,
            color_setting=color_setting,
            game_ended=False,
        )
    game_name = list(games.keys())[-1]
    fen = games[game_name]["fens"][-1]
    temp_board = chess.Board(fen)

    if local_play:
        player_color = "white"

    if (
        temp_board.is_checkmate()
        or temp_board.is_stalemate()
        or request.method == "POST"
        or "loss" in games[game_name]["result"].lower()
    ):

        new_game = True

        message = ""
        board = chess.Board()
        current_game = board
        if player_color == "black":
            print("player_color =", player_color)
            bot_move = get_bot_move(board)

            info_before = test_engine.analyse(board, chess.engine.Limit(time=0.02))
            best_move = info_before["pv"][0] if "pv" in info_before else None
            best_board = board.copy()
            best_board.push(best_move)
            best_info = test_engine.analyse(best_board, chess.engine.Limit(time=0.02))
            best_score = best_info["score"].white().score(mate_score=10000)
            board.push(bot_move)

            info_after = test_engine.analyse(board, chess.engine.Limit(time=0.02))
            after_score = (
                info_after["score"].white().score(mate_score=10000)
                if "score" in info_after
                else None
            )
            loss = abs(best_score - after_score)
            if bot_move == best_move:
                classification = "Best"

            elif loss <= 20:
                classification = "Excellent"

            elif loss <= 50:
                classification = "Good"

            elif loss <= 100:
                classification = "Inaccuracy"

            elif loss <= 300:
                classification = "Mistake"

            else:
                classification = "Blunder"
            if bot_move == best_move and len(info_before["pv"]) == 1:
                classification = "Great"

            bot_analysis = {
                "move": bot_move.uci(),
                "best_move": best_move.uci(),
                "classification": classification,
            }

    elif new_game:
        board = current_game

    else:
        white_time = games[game_name]["white_time"]
        black_time = games[game_name]["black_time"]
        if not local_play_button_pressed:
            local_play = games[game_name]["local_play"]
        local_play_button_pressed = False
        player_color = games[game_name]["player_color"]
        difficulty = games[game_name]["difficulty"]
        board = chess.Board(fen)

    message = ""

    resigned = False

    clean_white_time = format_time(white_time)
    clean_black_time = format_time(black_time)
    if white_time > 20000:
        clean_white_time = "∞"
        clean_black_time = "∞"
    print("In home fen:", board.fen())
    print("global local_play =", local_play)
    print(difficulty)
    print("white_time =", white_time)
    print("time in home:", format_time(int(white_time)), format_time(int(black_time)))

   
    saved_data["difficulty"] = difficulty
    saved_data["player_color"] = player_color
    saved_data["local_play"] = local_play
    saved_data["resigned"] = resigned
    saved_data["local_play_button_pressed"] = local_play_button_pressed
    saved_data["bot_analysis"] = bot_analysis
    saved_data["new_game"] = new_game
    saved_data["current_game"] = current_game.fen() if current_game else None

    
    with file_lock:
        with open(FILE_PATH, 'w') as f:
            json.dump(data, f, indent=4)

    return render_template(
        "home.html",
        fen=board.fen(),
        white_turn=board.turn,
        local_play=local_play,
        white_time=white_time,
        black_time=black_time,
        message=message,
        resigned=resigned,
        clock_started=False,
        clean_white_time=clean_white_time,
        clean_black_time=clean_black_time,
        elo=saved_data["elo"],
        username=username,
        difficulty=difficulty,
        color_setting=color_setting,
        game_ended=False,
    )


@app.route("/set_difficulty", methods=["POST"])
def set_difficulty():


    with open(FILE_PATH, "r") as f:
            data = json.load(f)
            saved_data = data["users"][session["username"]]
            difficulty = saved_data["difficulty"]
            bot_time = saved_data["bot_time"]
            

    difficulty = request.form["difficulty"]

    if difficulty == "beginner":
        bot_time = 0.001
    elif difficulty == "novice":
        bot_time = 0.003
    elif difficulty == "intermediate":
        bot_time = 0.01
    elif difficulty == "advanced":
        bot_time = 0.03
    elif difficulty == "master":
        bot_time = 0.1
    elif difficulty == "stockfish":
        bot_time = 1
    print(difficulty)


    
    saved_data["difficulty"] = difficulty
    saved_data["bot_time"] = bot_time
    
    with file_lock:
        with open(FILE_PATH, 'w') as f:
            json.dump(data, f, indent=4)

    return redirect("/")


@app.route("/set_color", methods=["POST"])
def set_color():
    
    
    with open(FILE_PATH, "r") as f:
            data = json.load(f)
            saved_data = data["users"][session["username"]]
            player_color = saved_data["player_color"]
            local_play_button_pressed = saved_data["local_play_button_pressed"]
            bot_analysis = saved_data["bot_analysis"]
            new_game = saved_data["new_game"]
            color_setting = saved_data["color_setting"]
            current_game = chess.Board(saved_data["current_game"]) if saved_data["current_game"] else None

    selected_color = request.form["color"]

    if new_game or saved_data["games"] == {}:
        player_color = selected_color
        color_setting = selected_color
        if player_color == "random":
            player_color = random.choice(["white", "black"])

        board = chess.Board()

        if player_color == "black":
            bot_move = get_bot_move(board)

            info_before = test_engine.analyse(board, chess.engine.Limit(time=0.02))
            best_move = info_before["pv"][0] if "pv" in info_before else None
            best_board = board.copy()
            best_board.push(best_move)
            best_info = test_engine.analyse(best_board, chess.engine.Limit(time=0.02))
            best_score = best_info["score"].white().score(mate_score=10000)
            board.push(bot_move)

            info_after = test_engine.analyse(board, chess.engine.Limit(time=0.02))
            after_score = (
                info_after["score"].white().score(mate_score=10000)
                if "score" in info_after
                else None
            )
            loss = abs(best_score - after_score)
            if bot_move == best_move:
                classification = "Best"

            elif loss <= 20:
                classification = "Excellent"

            elif loss <= 50:
                classification = "Good"

            elif loss <= 100:
                classification = "Inaccuracy"

            elif loss <= 300:
                classification = "Mistake"

            else:
                classification = "Blunder"
            if bot_move == best_move and len(info_before["pv"]) == 1:
                classification = "Great"

            bot_analysis = {
                "move": bot_move.uci(),
                "best_move": best_move.uci(),
                "classification": classification,
            }

        current_game = board
        new_game = True



    saved_data["player_color"] = player_color
    saved_data["local_play_button_pressed"] = local_play_button_pressed
    saved_data["bot_analysis"] = bot_analysis
    saved_data["new_game"] = new_game
    saved_data["color_setting"] = color_setting
    saved_data["current_game"] = current_game.fen() if current_game else None

    with file_lock:
        with open(FILE_PATH, 'w') as f:
            json.dump(data, f, indent=4)

    
    return redirect("/")


@app.route("/toggle_local_play", methods=["POST"])
def toggle_local_play():
    
    with open(FILE_PATH, "r") as f:
            data = json.load(f)
            saved_data = data["users"][session["username"]]
            local_play = saved_data["local_play"]
            local_play_button_pressed = saved_data["local_play_button_pressed"]
            

    local_play = not local_play
    local_play_button_pressed = True

    print(local_play)

    
    saved_data["local_play"] = local_play
    saved_data["local_play_button_pressed"] = local_play_button_pressed
    
    with file_lock:
        with open(FILE_PATH, 'w') as f:
            json.dump(data, f, indent=4)

    return redirect("/")


@app.route("/resign", methods=["POST"])
def resign():

    with open(FILE_PATH, "r") as f:
            data = json.load(f)
            saved_data = data["users"][session["username"]]
            difficulty = saved_data["difficulty"]
            player_color = saved_data["player_color"]
            local_play = saved_data["local_play"]
            resigned = saved_data["resigned"]


    print("resign")
    

    
    games = saved_data["games"]
    latest_game = list(games.keys())[-1]
    if player_color == "white":
        result = (
            f"Loss vs {difficulty.capitalize()}" if not local_play else "Black wins"
        )
    else:
        result = (
            f"Loss vs {difficulty.capitalize()}" if not local_play else "White wins"
        )
    games[latest_game]["result"] = result

    bot_elo = 0
    if difficulty == "beginner":
        bot_elo = 800
    elif difficulty == "novice":
        bot_elo = 1100
    elif difficulty == "intermediate":
        bot_elo = 1300
    elif difficulty == "advanced":
        bot_elo = 1800
    elif difficulty == "master":
        bot_elo = 2300
    elif difficulty == "stockfish":
        bot_elo = 3000
    player_elo = saved_data["elo"]
    elo_dif_minus = player_elo - bot_elo if player_elo >= bot_elo else 0
    elo_subtract = min(round(elo_dif_minus / 5), 100)

    saved_data["elo"] -= elo_subtract
    resigned = True
    

    saved_data["resigned"] = resigned

    with file_lock:
        with open(FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)

    
    return redirect("/")


@app.route("/save_clock", methods=["POST"])
def save_clock():

    with open(FILE_PATH, "r") as f:
            data1 = json.load(f)
            saved_data = data1["users"][session["username"]]
            difficulty = saved_data["difficulty"]
            bot_time = saved_data["bot_time"]
            player_color = saved_data["player_color"]
            local_play = saved_data["local_play"]
            resigned = saved_data["resigned"]
            time = saved_data["time"]
            local_play_button_pressed = saved_data["local_play_button_pressed"]
            bot_analysis = saved_data["bot_analysis"]
            new_game = saved_data["new_game"]
            color_setting = saved_data["color_setting"]
            current_game = chess.Board(saved_data["current_game"]) if saved_data["current_game"] else None
            puzzle_board = chess.Board(saved_data["puzzle_board"]) if saved_data["puzzle_board"] else None

    data = request.json

    games = saved_data["games"]
    if not games:
        return "", 204

    
    latest_game = list(games.keys())[-1]
    games[latest_game]["white_time"] = data["white_time"]
    games[latest_game]["black_time"] = data["black_time"]
    if data["white_time"] <= 0 or data["black_time"] <= 0:
        if local_play:
            if data["white_time"] == 0:
                games[latest_game]["result"] = "Black Wins"
            elif data["black_time"] == 0:
                games[latest_game]["result"] = "White Wins"
        else:

            if data["white_time"] == 0 and player_color == "white":
                games[latest_game]["result"] = f"Loss vs {difficulty.capitalize()}"
            elif data["black_time"] == 0 and player_color == "black":
                games[latest_game]["result"] = f"Loss vs {difficulty.capitalize()}"
            elif data["white_time"] == 0 and player_color == "black":
                games[latest_game]["result"] = f"Win vs {difficulty.capitalize()}"
            elif data["black_time"] == 0 and player_color == "white":
                games[latest_game]["result"] = f"Win vs {difficulty.capitalize()}"

    with file_lock:
        with open(FILE_PATH, "w") as f:
            json.dump(data1, f, indent=4)

    return {"success": True}


@app.route("/toggle_time", methods=["POST"])
def toggle_time():

    with open(FILE_PATH, "r") as f:
            data1 = json.load(f)
            saved_data = data1["users"][session["username"]]
            difficulty = saved_data["difficulty"]
            bot_time = saved_data["bot_time"]
            player_color = saved_data["player_color"]
            local_play = saved_data["local_play"]
            resigned = saved_data["resigned"]
            time = saved_data["time"]
            local_play_button_pressed = saved_data["local_play_button_pressed"]
            bot_analysis = saved_data["bot_analysis"]
            new_game = saved_data["new_game"]
            color_setting = saved_data["color_setting"]
            current_game = chess.Board(saved_data["current_game"]) if saved_data["current_game"] else None
            puzzle_board = chess.Board(saved_data["puzzle_board"]) if saved_data["puzzle_board"] else None

    data = request.form.get("time")
    print("Time:", data)
    time = data

    
    saved_data["time"] = time
    
    with file_lock:
        with open(FILE_PATH, "w") as f:
            json.dump(data1, f, indent=4)
    return redirect("/")


@app.route("/legal_moves", methods=["POST"])
def legal_moves():
    data = request.json
    square = data["square"]
    fen = data["fen"]
    print("Square:", square)
    print(repr(fen))

    board = chess.Board(fen)
    moves = [
        move.to_square
        for move in board.legal_moves
        if chess.square_name(move.from_square) == square
    ]
    return {"moves": [chess.square_name(sq) for sq in moves]}


@app.route("/move", methods=["POST"])
def move():
    
    
    print("MOVE ROUTE STARTED")
    with open(FILE_PATH, "r") as f:
            data = json.load(f)
            saved_data = data["users"][session["username"]]
            current_puzzle = saved_data["current_puzzle"]
            puzzle_index = saved_data["puzzle_index"]
            difficulty = saved_data["difficulty"]
            bot_time = saved_data["bot_time"]
            player_color = saved_data["player_color"]
            local_play = saved_data["local_play"]
            resigned = saved_data["resigned"]
            time = saved_data["time"]
            local_play_button_pressed = saved_data["local_play_button_pressed"]
            bot_analysis = saved_data["bot_analysis"]
            new_game = saved_data["new_game"]
            color_setting = saved_data["color_setting"]
            auto_skip = saved_data["auto_skip"]
            auto_skip_pressed = saved_data["auto_skip_pressed"]
            puzzle_completed = saved_data["puzzle_completed"]
            current_game = chess.Board(saved_data["current_game"]) if saved_data["current_game"] else None
            puzzle_board = chess.Board(saved_data["puzzle_board"]) if saved_data["puzzle_board"] else None

    print("current game in move:", current_game)
    data_move = request.json
    board = current_game if current_game else get_board()
    print("Board created")


    try:
        move = chess.Move.from_uci(data_move["move"])
        print(move)
    except Exception:
        print("Invalid Move")
        move = None
    message = ""

    if is_new_game(board):
        games = saved_data["games"]
        if games:
            last_number = max(int(name.split("_")[1]) for name in games.keys())
        else:
            last_number = 0
        game_name = f"game_{last_number + 1:03d}"
        saved_data["games"][game_name] = {
            "fens": [chess.STARTING_FEN],
            "orientation": player_color,
            "white_time": 300,
            "black_time": 300,
            "player_color": player_color,
            "local_play": local_play,
            "difficulty": difficulty,
        }
        saved_data["games"][game_name]["analysis"] = (
            [bot_analysis] if bot_analysis else []
        )
        current_game = None
        if board.fen() != chess.STARTING_FEN and not local_play:
            saved_data["games"][game_name]["fens"].append(board.fen())
    else:
        games = saved_data["games"]
        game_name = list(games.keys())[-1]

    print("Trying to use engine in move route")
    print(type(board))
    print(board.fen())
    print(board.is_valid())
    print(board)
    
    info_before = test_engine.analyse(board, chess.engine.Limit(time=0.02))
    
    print("Engine analysis finished in move route")

    
    if board.is_game_over():
        best_score = after_score
    else:
        best_move = info_before["pv"][0] if "pv" in info_before else None
        best_board = board.copy()
        best_board.push(best_move)
        best_info = test_engine.analyse(best_board, chess.engine.Limit(time=0.02))
        best_score = best_info["score"].white().score(mate_score=10000)

    if move in board.legal_moves:
        legal = True
        new_game = False
        board.push(move)
        print(board.fen())
        if board.is_check():
            message = "Check!"
            print("check")

        saved_data["games"][game_name]["fens"].append(board.fen())

        info_after = test_engine.analyse(board, chess.engine.Limit(time=0.02))
        after_score = (
            info_after["score"].white().score(mate_score=10000)
            if "score" in info_after
            else None
        )
        loss = abs(best_score - after_score)
        if move == best_move:
            classification = "Best"

        elif loss <= 20:
            classification = "Excellent"

        elif loss <= 50:
            classification = "Good"

        elif loss <= 100:
            classification = "Inaccuracy"

        elif loss <= 300:
            classification = "Mistake"

        else:
            classification = "Blunder"
        if move == best_move and len(info_before["pv"]) == 1:
            classification = "Great"

        print(move)
        saved_data["games"][game_name]["analysis"].append(
            {
                "move": move.uci(),
                "best_move": best_move.uci(),
                "classification": classification,
            }
        )
        info_before = test_engine.analyse(board, chess.engine.Limit(time=0.02))
        if board.is_game_over():
            best_score = after_score
        else:
            best_move = info_before["pv"][0] if "pv" in info_before else None
            best_board = board.copy()
            best_board.push(best_move)
            best_info = test_engine.analyse(best_board, chess.engine.Limit(time=0.02))
            best_score = best_info["score"].white().score(mate_score=10000)

        if not board.is_game_over() and not local_play:
            bot_move = get_bot_move(board)

            board.push(bot_move)
            print(board.fen())
            print(difficulty)
            saved_data["games"][game_name]["fens"].append(board.fen())

            info_after = test_engine.analyse(board, chess.engine.Limit(time=0.02))
            after_score = (
                info_after["score"].white().score(mate_score=10000)
                if "score" in info_after
                else None
            )
            loss = abs(best_score - after_score)
            if bot_move == best_move:
                classification = "Best"

            elif loss <= 20:
                classification = "Excellent"

            elif loss <= 50:
                classification = "Good"

            elif loss <= 100:
                classification = "Inaccuracy"

            elif loss <= 300:
                classification = "Mistake"

            else:
                classification = "Blunder"
            if bot_move == best_move and len(info_before["pv"]) == 1:
                classification = "Great"

            saved_data["games"][game_name]["analysis"].append(
                {
                    "move": bot_move.uci(),
                    "best_move": best_move.uci(),
                    "classification": classification,
                }
            )

    else:
        legal = False

    if board.is_check():
        message = "Check!"
        print("check")
    if board.is_game_over():
        if board.is_checkmate():
            print("checkmate")
            if board.turn == chess.BLACK:
                message = "Checkmate!\nWhite wins!"
                print(message)
            else:
                message = "Checkmate!\nBlack wins!"
        else:
            message = "Draw!"
    if message == "":
        message = None

    bot_elo = 0
    if difficulty == "beginner":
        bot_elo = 800
    elif difficulty == "novice":
        bot_elo = 1100
    elif difficulty == "intermediate":
        bot_elo = 1300
    elif difficulty == "advanced":
        bot_elo = 1800
    elif difficulty == "master":
        bot_elo = 2300
    elif difficulty == "stockfish":
        bot_elo = 3000
    player_elo = saved_data["elo"]
    elo_dif_plus = bot_elo - player_elo if bot_elo >= player_elo else 0
    elo_add = min(round(elo_dif_plus / 5), 100)
    elo_dif_minus = player_elo - bot_elo if player_elo >= bot_elo else 0
    elo_subtract = min(round(elo_dif_minus / 5), 100)

    game_ended = False

    if board.is_game_over():
        game_ended = True
        if board.is_checkmate():
            if local_play:
                if board.turn == chess.BLACK:
                    data_name = "White wins"
                else:
                    data_name = "Black wins"
            else:
                if (
                    player_color == "white"
                    and board.turn == chess.BLACK
                    or player_color == "black"
                    and board.turn == chess.WHITE
                ):
                    data_name = f"Win vs {difficulty.capitalize()}"
                    saved_data["elo"] += elo_add
                elif (
                    player_color == "white"
                    and board.turn == chess.WHITE
                    or player_color == "black"
                    and board.turn == chess.BLACK
                ):
                    data_name = f"Loss vs {difficulty.capitalize()}"
                    saved_data["elo"] -= elo_subtract
        else:
            print("Draw!")
            if local_play:
                data_name = "Draw"
            else:
                data_name = f"Draw vs {difficulty.capitalize()}"
            if bot_elo > player_elo:
                saved_data["elo"] += round(elo_add / 2)
            elif player_elo > bot_elo:
                saved_data["elo"] -= round(elo_subtract / 2)

    else:
        data_name = "In Progress"

    saved_data["games"][game_name]["result"] = data_name
    elo = saved_data["elo"]




    saved_data["current_game"] = current_game.fen() if current_game else None
    saved_data["new_game"] = new_game

    with file_lock:
        with open(FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)

    material = get_material(board)

    print("befor return in move:", board.fen())
    
    return {
        "legal": legal,
        "fen": board.fen(),
        "message": message,
        "local_play": local_play,
        "material": material,
        "white_turn": board.turn,
        "elo": elo,
        "game_ended": game_ended,
    }




@app.route("/puzzle_move", methods=["POST"])
def puzzle_move():
    try:
        with open(FILE_PATH, "r") as f:
            data = json.load(f)
            saved_data = data["users"][session["username"]]
            current_puzzle = saved_data["current_puzzle"]
            puzzle_index = saved_data["puzzle_index"]
            difficulty = saved_data["difficulty"]
            bot_time = saved_data["bot_time"]
            player_color = saved_data["player_color"]
            local_play = saved_data["local_play"]
            resigned = saved_data["resigned"]
            time = saved_data["time"]
            local_play_button_pressed = saved_data["local_play_button_pressed"]
            bot_analysis = saved_data["bot_analysis"]
            new_game = saved_data["new_game"]
            color_setting = saved_data["color_setting"]
            auto_skip = saved_data["auto_skip"]
            auto_skip_pressed = saved_data["auto_skip_pressed"]
            puzzle_completed = saved_data["puzzle_completed"]
            current_game = chess.Board(saved_data["current_game"]) if saved_data["current_game"] else None
            puzzle_board = chess.Board(saved_data["puzzle_board"]) if saved_data["puzzle_board"] else None

            streak = saved_data["puzzle_streak"]

    except Exception:
        with file_lock:
            with open(FILE_PATH, "w") as f:
                json.dump({"puzzle_streak": 0, "games": {}}, f, indent=4)
                streak = 0


    data_move = request.json
    correct_move = current_puzzle["moves"][puzzle_index]
    no_move = False
    try:
        move = chess.Move.from_uci(data_move["move"])
        print(move)
    except Exception:
        print("Invalid Move")
        move = None
        no_move = True

    print(correct_move)

    print(puzzle_board.turn)
    puzzle_completed = False
    if move in puzzle_board.legal_moves and move.uci() == correct_move:
        if puzzle_index + 1 < len(current_puzzle["moves"]):
            legal = True
            puzzle_board.push(move)
            puzzle_board.push(
                chess.Move.from_uci(current_puzzle["moves"][puzzle_index + 1])
            )
            correct = True
            puzzle_index += 2
            correct_move = current_puzzle["moves"][puzzle_index]
            puzzle_message = None
            puzzle_completed = False

        else:
            print("Puzzle Completed!")
            puzzle_completed = True
            legal = True
            correct = True
            puzzle_board.push(move)
            puzzle_message = "Puzzle Completed!"
            puzzle_completed = True
            streak += 1

    else:
        legal = False
        correct = False
        if move:
            puzzle_message = "Incorrect move! Try again."
        else:
            puzzle_message = ''
        if not no_move:
            streak = 0
    saved_data["puzzle_streak"] = streak


    message = None
    if puzzle_board.is_check():
        message = "Check!"
    if puzzle_board.is_checkmate():
        if puzzle_board.turn == chess.BLACK:
            message = "Checkmate!\nWhite wins!"
            print(message)
        else:
            message = "Checkmate!\nBlack wins!"
    if puzzle_board.is_stalemate():
        message = "Stalemate!\nDraw!"
    if puzzle_board is None:
        return {"error": "no puzzle loaded!"}
    if puzzle_message:
        message = puzzle_message
    
    skip_puzzle = False
    if puzzle_completed and auto_skip:
        skip_puzzle = True


    saved_data["current_puzzle"] = current_puzzle
    saved_data["puzzle_index"] = puzzle_index
    saved_data["puzzle_completed"] = puzzle_completed 
    saved_data["puzzle_board"] = puzzle_board.fen() if puzzle_board else None
    with file_lock:
        with open(FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)
    return {
        "legal": legal,
        "fen": puzzle_board.fen(),
        "message": message,
        "white_turn": puzzle_board.turn,
        "streak": streak,
        "correct_move": correct_move,
        "skip_puzzle": skip_puzzle
    }


@app.route("/history")
def history():
    if "username" not in session:
        return redirect("/login")
    with open(FILE_PATH, "r") as f:
        data = json.load(f)
        saved_data = data["users"][session["username"]]

    games = saved_data["games"]
    if games:
        latest_game = list(games.keys())[-1]
        games_to_delete = []
        for game_name, game_data in games.items():
            if "In Progress" in game_data["result"]:
                if game_name != latest_game:
                    games_to_delete.append(game_name)
        if games_to_delete:
            for game_name in games_to_delete:
                del games[game_name]

    with file_lock:
        with open(FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)

    games = dict(
        sorted(
            saved_data["games"].items(),
            key=lambda item: (
                not item[1].get("favorite", False),
                -int(item[0].split("_")[1]),
            ),
        )
    )
    
    return render_template("history.html", games=games)


@app.route("/delete_game/<game_name>", methods=["POST"])
def delete_game(game_name):

    with open(FILE_PATH, "r") as f:
        data = json.load(f)
        saved_data = data["users"][session["username"]]

        if game_name in saved_data["games"]:
            del saved_data["games"][game_name]

    with file_lock:
        with open(FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)
    return "", 204


@app.route("/rename_game", methods=["POST"])
def rename_game():
    data = request.json

    game_name = data["game_name"]
    new_name = data["new_name"]

    with open(FILE_PATH, "r") as f:
        data = json.load(f)
        saved_data = data["users"][session["username"]]

    saved_data["games"][game_name]["custom_name"] = new_name

    with file_lock:
        with open(FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)

    return "", 204


@app.route("/favorit_game/<game_name>", methods=["POST"])
def favorit_game(game_name):
    with open(FILE_PATH, "r") as f:
        data = json.load(f)
        saved_data = data["users"][session["username"]]

    saved_data["games"][game_name]["favorite"] = not saved_data["games"][game_name].get(
        "favorite", False
    )

    with file_lock:
        with open(FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)

    return "", 204


@app.route("/puzzles")
def puzzles():
    if "username" not in session:
        return redirect("/login")
    
    with open(FILE_PATH, "r") as f:
            data = json.load(f)
            saved_data = data["users"][session["username"]]
            current_puzzle = saved_data["current_puzzle"]
            puzzle_index = saved_data["puzzle_index"]
            difficulty = saved_data["difficulty"]
            bot_time = saved_data["bot_time"]
            player_color = saved_data["player_color"]
            local_play = saved_data["local_play"]
            resigned = saved_data["resigned"]
            time = saved_data["time"]
            local_play_button_pressed = saved_data["local_play_button_pressed"]
            bot_analysis = saved_data["bot_analysis"]
            new_game = saved_data["new_game"]
            color_setting = saved_data["color_setting"]
            auto_skip = saved_data["auto_skip"]
            auto_skip_pressed = saved_data["auto_skip_pressed"]
            puzzle_completed = saved_data["puzzle_completed"]
            current_game = chess.Board(saved_data["current_game"]) if saved_data["current_game"] else None
            puzzle_board = chess.Board(saved_data["puzzle_board"]) if saved_data["puzzle_board"] else None

            streak = saved_data['puzzle_streak']

    
    turn_message = ''
    
    

    with open(FILE_PATH1, "r") as f:

        if auto_skip_pressed and not puzzle_completed:
            auto_skip_pressed = False
        else:
            puzzle_completed = False

            puzzles = json.load(f)
            current_puzzle = random.choice(puzzles)

            
            puzzle_index = 0
            puzzle_board = chess.Board(current_puzzle["fen"])

            turn_message = (
                "White to move" if puzzle_board.turn == chess.WHITE else "Black to move"
            )

            streak = saved_data["puzzle_streak"]
        
        correct_move = current_puzzle["moves"][puzzle_index]

        saved_data["current_puzzle"] = current_puzzle
        saved_data["puzzle_index"] = puzzle_index
        saved_data["auto_skip_pressed"] = auto_skip_pressed
        saved_data["puzzle_completed"] = puzzle_completed 
        saved_data["puzzle_board"] = puzzle_board.fen() if puzzle_board else None
        with file_lock:
            with open(FILE_PATH, "w") as f:
                json.dump(data, f, indent=4)

        if auto_skip_pressed:
            return render_template(
                "puzzles.html",
                fen=puzzle_board.fen(),
                white_turn=puzzle_board.turn,
                turn_message=turn_message,
                streak=streak,
                correct_move=correct_move,
                auto_skip=auto_skip
            )

        return render_template(
            "puzzles.html",
            fen=puzzle_board.fen(),
            white_turn=puzzle_board.turn,
            turn_message=turn_message,
            streak=streak,
            correct_move=correct_move,
            auto_skip=auto_skip
        )

@app.route('/end_streak')
def end_streak():

    print('streak ended')

    with open(FILE_PATH, 'r') as f:
        data = json.load(f)
        saved_data = data["users"][session["username"]]

    saved_data["puzzle_streak"] = 0

    with file_lock:
        with open(FILE_PATH, 'w') as f:
            json.dump(data, f, indent=4)
    return {"streak": 0}

@app.route('/toggle_auto_skip', methods=["POST"])
def toggle_auto_skip():
    with open(FILE_PATH, "r") as f:
            data = json.load(f)
            saved_data = data["users"][session["username"]]
            auto_skip = saved_data["auto_skip"]
            auto_skip_pressed = saved_data["auto_skip_pressed"]



    auto_skip_pressed = True
    auto_skip = not auto_skip
    print('Auto Skip:', auto_skip)

    
    saved_data["auto_skip"] = auto_skip
    saved_data["auto_skip_pressed"] = auto_skip_pressed
    with file_lock:
            with open(FILE_PATH, "w") as f:
                json.dump(data, f, indent=4)
    return redirect('/puzzles')

@app.errorhandler(Exception)
def handle_error(e):
    import traceback
    traceback.print_exc()
    return str(e), 500

if __name__ == "__main__":
    app.run(debug=True)

"Bugs: "

"Ideas: put it up online"


"if ever you stumble upon a bug that doesnt seem to have a problem, end task on python.exe in task manager details."
