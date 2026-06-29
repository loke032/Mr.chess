let fadeTimeout;
if (turnMessage) {
    msg = document.getElementById('message');
msg.innerText = turnMessage;
msg.classList.add('show');
clearTimeout(fadeTimeout);
fadeTimeout = setTimeout(() => {
    msg.classList.remove('show');
}, 1500);
}


var config = {
        draggable: true,
        dropOFFBoard: 'snapback',
        onDragStart: ondragStart,
        position: currentFen,
        orientation: whiteTurn ? 'white' : 'black',
        pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png',

        onDrop: function(source, target, piece) {
            document.querySelectorAll(".move-dot").forEach(dot => dot.remove());
            var move = source + target;
            
            
            if (piece[1] === 'P' && (target[1] === '8' || target[1] === '1')) {
                move += 'q';
                
            }
            let fadeTimeout;

            fetch('/puzzle_move', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    move: move
                })
            })
            .then(response => response.json())
            .then(data => {
                correct_move = data.correct_move
                currentFen = data.fen
                document.getElementById('streak').innerText = `${data.streak}🔥`;
                board.position(data.fen);

                if (data.skip_puzzle) {
                    window.location.href = ('/puzzles')
                }

                if (data.message.includes('Checkmate') || data.message.includes('Stalemate')) {
                    document.getElementById('checkmate-message').innerText = data.message;
                    const msg = document.getElementById('message');
                    msg.style.opacity = 0; 
                } else {
                    
                    const msg = document.getElementById('message');

                    msg.innerText = data.message;
                    msg.classList.add('show');
                    clearTimeout(fadeTimeout);
                    fadeTimeout = setTimeout(() => {
                        msg.classList.remove('show');
                    }, 1500);
                }
            });
        }
    };
    
    board = Chessboard("board", config);


function ondragStart(source, piece) {
    showLegalMoves(source);
}

function showLegalMoves(square) {
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

function showHint() {
    console.log(correct_move)
    const msg = document.getElementById('message')

    msg.innerText = correct_move;
    msg.classList.add('show');
    clearTimeout(fadeTimeout);
    fadeTimeout = setTimeout(() => {
        msg.classList.remove('show');
    }, 1500);

    fetch('/end_streak')
        .then(response => response.json())
        .then(data => {
            document.getElementById('streak').innerText = `0🔥`;
    });
    }


let enabled = false;
        const button = document.getElementById('auto-skip');
        button.addEventListener('click', () => {
            enabled = !enabled;
            if (enabled) {
                button.textContent = 'Auto Skip: On';
            } else {
                button.textContent = 'Auto Skip: Off';
            }
        })