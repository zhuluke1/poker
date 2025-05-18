from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from poker_game import PokerGame
from player import Player
from hand_evaluator import HandEvaluator
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Game state
game = None
players = {}
MAX_PLAYERS = 6

def get_game_state():
    """Convert game state to JSON-serializable format"""
    global game
    if not game:
        return None
        
    return {
        'pot': game.pot,
        'community_cards': [
            {'suit': card.suit.name, 'value': card.value}
            for card in game.community_cards
        ],
        'players': [
            {
                'name': player.name,
                'chips': player.chips,
                'bet': player.bet,
                'hand': [
                    {'suit': card.suit.name, 'value': card.value}
                    for card in player.hand
                ] if not player.folded else [],
                'is_current': i == game.current_player_index
            }
            for i, player in enumerate(game.players)
        ],
        'dealer_position': game.dealer_position,
        'current_player_index': game.current_player_index
    }

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    logger.debug(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    global game, players
    logger.debug(f'Client disconnected: {request.sid}')
    if request.sid in players:
        player_name = players[request.sid]
        del players[request.sid]
        emit('game_message', f'{player_name} has left the game', broadcast=True)
        
        # If game exists, remove the player
        if game:
            game.players = [p for p in game.players if p.name != player_name]
            if len(game.players) < 2:
                # Not enough players, reset the game
                game = None
                emit('game_message', 'Game reset due to insufficient players', broadcast=True)
            else:
                # Update game state for remaining players
                emit('game_state', get_game_state(), broadcast=True)
        
        # Send lobby update to all clients
        lobby_players = [{'name': name, 'ready': False} for name in players.values()]
        emit('lobby_update', lobby_players, broadcast=True)

@socketio.on('join_game')
def handle_join_game(data):
    global game, players
    logger.debug(f'Join game request from {request.sid}: {data}')
    try:
        if len(players) >= MAX_PLAYERS:
            emit('game_message', 'Game is full')
            return
            
        player_name = data['name']
        # Check if name is already taken by existing players
        if player_name in players.values():
            emit('game_message', 'Name already taken')
            return
            
        # Check if name is taken by players in the game
        if game and any(p.name == player_name for p in game.players):
            emit('game_message', 'Name already taken')
            return
            
        players[request.sid] = player_name
        
        if not game:
            # Create new game with first player
            game = PokerGame([Player(player_name)])
            emit('game_message', f'{player_name} has joined the game')
        else:
            # Add player to existing game
            game.players.append(Player(player_name))
            emit('game_message', f'{player_name} has joined the game')
        
        # Send lobby update to all clients
        lobby_players = [{'name': name, 'ready': False} for name in players.values()]
        emit('lobby_update', lobby_players, broadcast=True)
        
        # Send initial game state
        emit('game_state', get_game_state(), broadcast=True)
    except Exception as e:
        logger.error(f'Error in join_game: {str(e)}')
        emit('game_message', 'An error occurred while joining the game')

@socketio.on('start_game')
def handle_start_game():
    global game
    if not game or request.sid not in players:
        return
        
    player_name = players[request.sid]
    # Only the first player can start the game
    if game.players[0].name != player_name:
        return
        
    if len(game.players) >= 2 and not game.is_hand_in_progress:
        logger.debug('Starting new hand with two players')
        game.start_hand()
        emit('game_started', broadcast=True)
        emit('game_state', get_game_state(), broadcast=True)
        # Notify the first player to act (small blind in heads-up)
        first_player = game.players[game.current_player_index]
        for sid, name in players.items():
            if name == first_player.name:
                emit('your_turn', room=sid)
                break

@socketio.on('player_action')
def handle_player_action(data):
    global game
    if not game or request.sid not in players:
        return
        
    player_name = players[request.sid]
    player_index = next(i for i, p in enumerate(game.players) if p.name == player_name)
    
    if player_index != game.current_player_index:
        emit('not_your_turn')
        return
    
    action = data['action']
    if action == 'fold':
        game.players[player_index].fold()
    elif action == 'call':
        amount = game.minimum_bet - game.players[player_index].bet
        game.players[player_index].place_bet(amount)
        game.pot += amount
    elif action == 'raise':
        amount = data['amount']
        if amount >= game.minimum_bet * 2:
            game.players[player_index].place_bet(amount)
            game.pot += amount
            game.minimum_bet = amount
        else:
            emit('game_message', 'Invalid raise amount')
            return
    
    # Check if the current betting round is complete
    if game.is_hand_complete():
        # Count active players (not folded)
        active_players = [p for p in game.players if not p.folded]
        
        if len(active_players) <= 1:
            # Only one player left, they win the pot
            winner = active_players[0]
            winner.chips += game.pot
            emit('game_message', f'{winner.name} wins ${game.pot} (everyone else folded)', broadcast=True)
            
            game.end_hand()
            game.start_hand()
            emit('game_message', 'Starting new hand', broadcast=True)
        else:
            # Reset bets for the next round
            for player in game.players:
                player.bet = 0
            game.minimum_bet = game.big_blind
            
            # Deal next round of community cards
            if len(game.community_cards) == 0:
                # Deal flop
                game.deal_community_cards(3)
                emit('game_message', 'Dealing the flop', broadcast=True)
            elif len(game.community_cards) == 3:
                # Deal turn
                game.deal_community_cards(1)
                emit('game_message', 'Dealing the turn', broadcast=True)
            elif len(game.community_cards) == 4:
                # Deal river
                game.deal_community_cards(1)
                emit('game_message', 'Dealing the river', broadcast=True)
            else:
                # End of hand
                winners = game.get_winners()
                pot_per_winner = game.pot // len(winners)
                
                for winner in winners:
                    winner.chips += pot_per_winner
                    rank, kickers = HandEvaluator.evaluate_hand(winner.hand, game.community_cards)
                    hand_name = HandEvaluator.get_hand_name(rank)
                    emit('game_message', f'{winner.name} wins ${pot_per_winner} with {hand_name}', broadcast=True)
                
                game.end_hand()
                game.start_hand()
                emit('game_message', 'Starting new hand', broadcast=True)
        
        # Set current player for next round
        if len(game.players) == 2:  # Heads-up play
            if len(game.community_cards) == 0:
                # Pre-flop: Small blind (dealer) acts first
                game.current_player_index = game.dealer_position
            else:
                # Post-flop: Big blind acts first
                game.current_player_index = (game.dealer_position + 1) % 2
        else:  # Regular play
            # First to act is after the dealer
            game.current_player_index = (game.dealer_position + 1) % len(game.players)
            while game.players[game.current_player_index].folded:
                game.current_player_index = (game.current_player_index + 1) % len(game.players)
    else:
        # Move to next player in current round
        game.next_player()
    
    # Update game state
    emit('game_state', get_game_state(), broadcast=True)
    
    # Notify next player
    if game.current_player_index is not None:
        next_player = game.players[game.current_player_index]
        for sid, name in players.items():
            if name == next_player.name:
                emit('your_turn', room=sid)
                break

if __name__ == '__main__':
    socketio.run(app, debug=True) 