const socket = io();
let playerName = '';
let isMyTurn = false;

// Debug logging
function log(message) {
    console.log(`[Poker Game] ${message}`);
}

// DOM Elements
const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
const gameControls = document.getElementById('game-controls');
const gameMessages = document.getElementById('game-messages');
const raiseSlider = document.getElementById('raise-slider');
const raiseAmount = document.getElementById('raise-amount');
const potAmount = document.getElementById('pot-amount');

// Show login modal on page load
document.addEventListener('DOMContentLoaded', () => {
    log('Page loaded, showing login modal');
    loginModal.show();
});

// Socket connection events
socket.on('connect', () => {
    log('Connected to server');
});

socket.on('connect_error', (error) => {
    log(`Connection error: ${error}`);
    showMessage('Failed to connect to server');
});

socket.on('disconnect', () => {
    log('Disconnected from server');
    showMessage('Disconnected from server');
});

// Handle login form submission
document.getElementById('login-form').addEventListener('submit', (e) => {
    e.preventDefault();
    playerName = document.getElementById('player-name').value;
    log(`Attempting to join game as ${playerName}`);
    socket.emit('join_game', { name: playerName });
    loginModal.hide();
});

// Game control buttons
document.getElementById('fold-btn').addEventListener('click', () => {
    if (isMyTurn) {
        socket.emit('player_action', { action: 'fold' });
    }
});

document.getElementById('check-call-btn').addEventListener('click', () => {
    if (isMyTurn) {
        socket.emit('player_action', { action: 'call' });
    }
});

document.getElementById('raise-btn').addEventListener('click', () => {
    if (isMyTurn) {
        const amount = parseInt(raiseSlider.value);
        socket.emit('player_action', { action: 'raise', amount });
    }
});

// Update raise amount display
raiseSlider.addEventListener('input', () => {
    raiseAmount.textContent = raiseSlider.value;
});

// Socket event handlers
socket.on('game_state', (state) => {
    log('Received game state update');
    updateGameState(state);
});

socket.on('your_turn', () => {
    log('It is your turn');
    isMyTurn = true;
    gameControls.style.display = 'block';
});

socket.on('not_your_turn', () => {
    log('Not your turn');
    isMyTurn = false;
    gameControls.style.display = 'none';
});

socket.on('game_message', (message) => {
    log(`Game message: ${message}`);
    showMessage(message);
});

// Update game state
function updateGameState(state) {
    // Update pot
    potAmount.textContent = state.pot;

    // Update community cards
    updateCommunityCards(state.community_cards);

    // Update players
    updatePlayers(state.players, state.dealer_position);

    // Update dealer button
    updateDealerButton(state.dealer_position);
}

function updateCommunityCards(cards) {
    const slots = ['flop1', 'flop2', 'flop3', 'turn', 'river'];
    slots.forEach((slotId, index) => {
        const slot = document.getElementById(slotId);
        if (index < cards.length) {
            slot.innerHTML = createCardHTML(cards[index]);
        } else {
            slot.innerHTML = '';
        }
    });
}

function updatePlayers(players, dealerPosition) {
    const container = document.querySelector('.players-container');
    container.innerHTML = '';

    players.forEach((player, index) => {
        const playerDiv = document.createElement('div');
        playerDiv.className = `player ${player.is_current ? 'active' : ''}`;
        playerDiv.id = `player${index}`;

        // Add dealer button if this is the dealer position
        const dealerButton = index === dealerPosition ? 
            '<div class="dealer-button">D</div>' : '';

        playerDiv.innerHTML = `
            <div class="player-info">
                ${dealerButton}
                <div class="player-name">${player.name}</div>
                <div class="player-chips">$${player.chips}</div>
                <div class="player-bet">Bet: $${player.bet}</div>
            </div>
            <div class="player-cards">
                ${player.hand.map(card => createCardHTML(card)).join('')}
            </div>
        `;

        container.appendChild(playerDiv);
    });
}

function updateDealerButton(dealerPosition) {
    const players = document.querySelectorAll('.player');
    players.forEach((player, index) => {
        const dealerButton = player.querySelector('.dealer-button');
        if (index === dealerPosition) {
            if (!dealerButton) {
                const button = document.createElement('div');
                button.className = 'dealer-button';
                button.textContent = 'D';
                player.appendChild(button);
            }
        } else if (dealerButton) {
            dealerButton.remove();
        }
    });
}

function createCardHTML(card) {
    if (!card) return '<div class="card-slot"></div>';
    
    const suitSymbols = {
        'HEARTS': '♥',
        'DIAMONDS': '♦',
        'CLUBS': '♣',
        'SPADES': '♠'
    };

    const valueStr = {
        11: 'J',
        12: 'Q',
        13: 'K',
        14: 'A'
    }[card.value] || card.value;

    return `
        <div class="card ${card.suit.toLowerCase()}">
            ${valueStr}${suitSymbols[card.suit]}
        </div>
    `;
}

function showMessage(message) {
    gameMessages.textContent = message;
    gameMessages.style.display = 'block';
    setTimeout(() => {
        gameMessages.style.display = 'none';
    }, 3000);
} 