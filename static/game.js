const socket = io({
    transports: ['websocket'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});

let playerName = '';
let isMyTurn = false;
let isGameStarted = false;

// Debug logging
function log(message) {
    console.log(`[Poker Game] ${message}`);
}

// DOM Elements
const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
const gameControls = document.getElementById('game-controls');
const gameControlsLobby = document.getElementById('game-controls-lobby');
const gameMessages = document.getElementById('game-messages');
const playerList = document.getElementById('player-list');
const startGameBtn = document.getElementById('start-game-btn');
const raiseSlider = document.getElementById('raise-slider');
const raiseAmount = document.getElementById('raise-amount');
const potAmount = document.getElementById('pot-amount');

// Show login modal on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, showing login modal');
    loginModal.show();
});

// Socket connection events
socket.on('connect', () => {
    console.log('Connected to server');
    showMessage('Connected to server');
});

socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    showMessage('Failed to connect to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    showMessage('Disconnected from server');
    gameControls.style.display = 'none';
    gameControlsLobby.style.display = 'none';
});

socket.on('reconnect', (attemptNumber) => {
    console.log('Reconnected after', attemptNumber, 'attempts');
    showMessage('Reconnected to server');
    if (playerName) {
        socket.emit('join_game', { name: playerName });
    }
});

// Handle login form submission
document.getElementById('login-form').addEventListener('submit', (e) => {
    e.preventDefault();
    playerName = document.getElementById('player-name').value.trim();
    if (!playerName) {
        showMessage('Please enter a name');
        return;
    }
    console.log(`Attempting to join game as ${playerName}`);
    socket.emit('join_game', { name: playerName });
    loginModal.hide();
});

// Start game button handler
startGameBtn.addEventListener('click', () => {
    socket.emit('start_game');
});

// Game control buttons
document.getElementById('fold-btn').addEventListener('click', () => {
    if (isMyTurn) {
        socket.emit('player_action', { action: 'fold' });
        isMyTurn = false;
        gameControls.style.display = 'none';
    }
});

document.getElementById('check-call-btn').addEventListener('click', () => {
    if (isMyTurn) {
        socket.emit('player_action', { action: 'call' });
        isMyTurn = false;
        gameControls.style.display = 'none';
    }
});

document.getElementById('raise-btn').addEventListener('click', () => {
    if (isMyTurn) {
        const amount = parseInt(raiseSlider.value);
        socket.emit('player_action', { action: 'raise', amount });
        isMyTurn = false;
        gameControls.style.display = 'none';
    }
});

// Update raise amount display
raiseSlider.addEventListener('input', () => {
    raiseAmount.textContent = raiseSlider.value;
});

// Socket event handlers
socket.on('game_state', (state) => {
    console.log('Received game state:', state);
    if (!state) {
        console.warn('Received null game state');
        showMessage('Game not available');
        return;
    }
    console.log('Valid game state received, updating UI.');
    updateGameState(state);
});

socket.on('lobby_update', (players) => {
    console.log('Lobby update received:', players);
    updateLobby(players);
});

socket.on('game_started', () => {
    console.log('Game started event received');
    isGameStarted = true;
    gameControlsLobby.style.display = 'none';
    showMessage('Game started!');
});

socket.on('your_turn', () => {
    console.log('Your turn event received');
    showMessage('It\'s your turn');
    isMyTurn = true;
    gameControls.style.display = 'block';
});

socket.on('not_your_turn', () => {
    console.log('Not your turn');
    isMyTurn = false;
    gameControls.style.display = 'none';
});

socket.on('game_message', (message) => {
    console.log('Game message:', message);
    showMessage(message);
});

// Update game state
function updateGameState(state) {
    console.log('Executing updateGameState with state:', state);
    
    // Update game started status
    isGameStarted = state.community_cards.length > 0 || state.players.some(player => player.hand.length > 0);
    console.log('isGameStarted set to:', isGameStarted);
    
    // Update pot
    document.getElementById('pot').textContent = `Pot: $${state.pot}`;
    console.log('Pot updated to:', state.pot);
    
    // Update community cards
    console.log('Updating community cards with:', state.community_cards);
    updateCommunityCards(state.community_cards);
    
    // Update players
    console.log('Updating players with:', state.players);
    updatePlayers(state.players, state.dealer_position);
    
    // Show/hide game controls based on whether it's the player's turn
    const gameControls = document.getElementById('game-controls');
    // Find the current player object in the state's players array
    const currentPlayer = state.players.find(player => player.is_current);

    console.log('Current player based on state:', currentPlayer);
    console.log('Current playerName (local):', playerName);

    if (currentPlayer && currentPlayer.name === playerName) {
        console.log('It is this client\'s turn, showing controls.');
        gameControls.style.display = 'block';
        // Update raise slider max value based on current player chips and bet
        const maxRaise = currentPlayer.chips + currentPlayer.bet;
        const raiseSlider = document.getElementById('raise-slider');
        const raiseAmountSpan = document.getElementById('raise-amount');
        
        console.log('Updating raise slider. Max raise:', maxRaise, 'Min bet:', state.minimum_bet);

        raiseSlider.max = maxRaise;
        // Set default raise to minimum bet from the state
        raiseSlider.value = state.minimum_bet;
        raiseAmountSpan.textContent = `$${state.minimum_bet}`;
    } else {
        console.log('Not this client\'s turn, hiding controls.');
        gameControls.style.display = 'none';
    }
}

function updateCommunityCards(cards) {
    console.log('Executing updateCommunityCards with cards:', cards);
    const slots = ['flop1', 'flop2', 'flop3', 'turn', 'river'];
    slots.forEach((slotId, index) => {
        const slot = document.getElementById(slotId);
        slot.innerHTML = ''; // Clear previous card
        if (index < cards.length) {
            console.log(`Rendering community card ${index}:`, cards[index]);
            // Create and append card element if a card exists for this slot
            const cardElement = createCardHTML(cards[index]);
            slot.appendChild(cardElement);
        } else {
            console.log(`Clearing community card slot ${index}`);
             // Optionally add an empty card slot visual if needed, but clearing is fine for now
        }
    });
     console.log('Finished updating community cards.');
}

function updatePlayers(players, dealerPosition) {
     console.log('Executing updatePlayers with players:', players, 'Dealer position:', dealerPosition);
    const container = document.querySelector('.players-container');
    container.innerHTML = '';

    players.forEach((player, index) => {
        console.log(`Rendering player ${index}:`, player);
        const playerDiv = document.createElement('div');
        playerDiv.className = `player ${player.is_current ? 'active' : ''}`;
        playerDiv.id = `player${index}`;

        // Add dealer button if this is the dealer position
        const dealerButtonHTML = index === dealerPosition ? 
            '<div class="dealer-button">D</div>' : '';

        playerDiv.innerHTML = `
            <div class="player-info">
                ${dealerButtonHTML}
                <div class="player-name">${player.name}</div>
                <div class="player-chips">$${player.chips}</div>
                <div class="player-bet">Bet: $${player.bet}</div>
            </div>
            <div class="player-cards">
                ${player.hand.map(card => createCardHTML(card)).join('')}
            </div>
        `;

        container.appendChild(playerDiv);
         console.log(`Player ${index} rendered.`);
    });
     console.log('Finished updating players.');
}

function createCardHTML(card) {
     console.log('Executing createCardHTML for card:', card);
    if (!card) return ''; // Return empty string for empty slots in player hands
    
    const suitSymbols = {
        'HEARTS': '♥',
        'DIAMONDS': '♦',
        'CLUBS': '♣',
        'SPADES': '♠'
    };

    const valueMap = {
        11: 'J',
        12: 'Q',
        13: 'K',
        14: 'A'
    };

    const valueStr = valueMap[card.value] || card.value;
    const suitSymbol = suitSymbols[card.suit];

    const cardHTML = `
        <div class="card ${card.suit.toLowerCase()}">
            <div class="card-content">
                <div class="card-value">${valueStr}</div>
                <div class="suit-symbol">${suitSymbol}</div>
            </div>
        </div>
    `;
    console.log('Generated card HTML:', cardHTML);
    return cardHTML;
}

function showMessage(message) {
    gameMessages.textContent = message;
    gameMessages.style.display = 'block';
    setTimeout(() => {
        gameMessages.style.display = 'none';
    }, 3000);
}

// Update lobby display
function updateLobby(players) {
    playerList.innerHTML = '';
    players.forEach(player => {
        const playerDiv = document.createElement('div');
        playerDiv.className = `player-list-item ${player.ready ? 'ready' : ''}`;
        playerDiv.innerHTML = `
            <span>${player.name}</span>
            <span>${player.ready ? 'Ready' : 'Waiting'}</span>
        `;
        playerList.appendChild(playerDiv);
    });

    // Show start game button if player is the first one and game hasn't started
    if (!isGameStarted && players.length >= 2 && players[0].name === playerName) {
        gameControlsLobby.style.display = 'block';
    } else {
        gameControlsLobby.style.display = 'none';
    }
} 