let gameOver = false;


var config = {
        draggable: true,
        dropOFFBoard: 'snapback',
        position: currentFen,
        onDragStart: ondragStart,
        orientation: whiteTurn ? 'white' : 'black',
        pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png',

        onDrop: function(source, target, piece) {
            console.log("onDrop called");
            document.querySelectorAll(".move-dot").forEach(dot => dot.remove());
            if (gameOver || resigned) return 'snapback';
            var move = source + target;
            
            
            if (piece[1] === 'P' && (target[1] === '8' || target[1] === '1')) {
                move += 'q';
                
            }
            let fadeTimeout;
            console.log(board.fen());
            console.log("sending move:", move);
            fetch('/move', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    move: move,
                    
                })
            })
            .then(response => response.json())
            .then(data => {
                game_ended = data.game_ended;

                board.position(data.fen);
                currentFen = data.fen
                console.log('Fen just after /move return: ', currentFen)

                if (!clockStarted) {
                    clockStarted = true;
                }

                
                board.position(data.fen);

                document.querySelectorAll(".move-dot").forEach(dot => dot.remove());

                const material = document.getElementById('material');
                material.innerText = `Material: ${data.material}`;

                if (data.local_play && data.legal) {
                    board.flip();
                }
                if (data.message && (data.message.includes('Checkmate') || data.message.includes('Stalemate'))) {
                    document.getElementById('checkmate-message').innerText = data.message;
                    const msg = document.getElementById('message');
                    msg.style.opacity = 0;
                    document.getElementById('elo').innerText = `Elo: ${data.elo}`;
                } else if (data.message) {
                    
                    const msg = document.getElementById('message');

                    msg.innerText = data.message;
                    msg.classList.add('show');
                    clearTimeout(fadeTimeout);
                    fadeTimeout = setTimeout(() => {
                        msg.classList.remove('show');
                    }, 1500);
                }
                whiteTurn = data.white_turn;
                console.log("White's turn:", whiteTurn);
            });
        }
    };
    
    board = Chessboard("board", config);
    document.addEventListener("contextmenu", function (e) {
        if (e.target.closest("#board")) {
            e.preventDefault();
        }
    });


console.log(whiteTime)
console.log(blackTime)
let saveCounter = 0;
setInterval(function() {
    
    if (whiteTime > 0 && blackTime > 0 && !(gameOver && resigned && game_ended)) {
        if (!clockStarted) {
        return;
    }
        if (whiteTurn) {
            whiteTime--;
        } else {
            blackTime--;
        }
    if (!(whiteTime > 20000 || blackTime > 20000)) {
        document.getElementById('white-clock').innerText = whiteTime < 0 ? '00:00' : `${Math.floor(whiteTime / 60).toString().padStart(2, '0')}:${(whiteTime % 60).toString().padStart(2, '0')}`;
        document.getElementById('black-clock').innerText = blackTime < 0 ? '00:00' : `${Math.floor(blackTime / 60).toString().padStart(2, '0')}:${(blackTime % 60).toString().padStart(2, '0')}`;
    }
    else {
        document.getElementById('white-clock').innerText = '∞';
        document.getElementById('black-clock').innerText = '∞';
    }
    if (whiteTime <= 0 || blackTime <= 0) {
        console.log(whiteTime)
        if (whiteTime <= 0) {
            console.log("White time ran out");
            gameOver = true;
            document.getElementById('checkmate-message').innerText = 'Black wins on time!';
        }
        if (blackTime <= 0) {
            gameOver = true;
            document.getElementById('checkmate-message').innerText = 'White wins on time!';
        }}
    
    else {
        gameOver = false; }
    
    saveCounter++;

    if (saveCounter >= 10) {
        saveCounter = 0;
    
    
        fetch('/save_clock', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                white_time: whiteTime,
                black_time: blackTime
            })
        });
    }
    }}, 1000);
    

let enabled = false;
        const button = document.getElementById('local-play-button');
        button.addEventListener('click', () => {
            enabled = !enabled;
            if (enabled) {
                button.textContent = 'Local Play: On';
            } else {
                button.textContent = 'Local Play: Off';
            }
        })



function ondragStart(source, piece) {
    showLegalMoves(source);
}



function showLegalMoves(square) {
    console.log('Fen sending to legal_moves', currentFen)
    fetch('/legal_moves', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            square: square,
            fen: currentFen
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.moves)
        document.querySelectorAll(".move-dot").forEach(dot => dot.remove());
        data.moves.forEach(target => {
            const squareEl = document.querySelector(`.square-${target}`);
            if (!squareEl) return;
            const dot = document.createElement('div');
            dot.classList.add('move-dot');
            squareEl.appendChild(dot);
        });
    });
}

        
window.onload = function() {
    const scrollY = localStorage.getItem('scroll-position');
    if (scrollY !== null) {
        window.scrollTo(0, parseInt(scrollY));
    }
};

window.onbeforeunload = function() {
    localStorage.setItem('scroll-position', window.scrollY);
};