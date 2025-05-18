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
        'current_player_index': game.current_player_index,
        'minimum_bet': game.minimum_bet
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
                game = None
                emit('game_message', 'Game reset due to insufficient players', broadcast=True)
            else:
                emit('game_state', get_game_state(), broadcast=True)

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
        if player_name in players.values():
            emit('game_message', 'Name already taken')
            return

        if game and any(p.name == player_name for p in game.players):
            emit('game_message', 'Name already taken')
            return

        players[request.sid] = player_name

        if not game:
            game = PokerGame([Player(player_name)])
            emit('game_message', f'{player_name} has joined the game')
        else:
            game.players.append(Player(player_name))
            emit('game_message', f'{player_name} has joined the game')

        lobby_players = [{'name': name, 'ready': game is not None and game.is_hand_in_progress} for name in players.values()]
        emit('lobby_update', lobby_players, broadcast=True)
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
    if game.players[0].name != player_name:
        return

    if len(game.players) >= 2 and not game.is_hand_in_progress:
        logger.debug('Starting new hand with two players')
        game.start_hand()
        emit('game_started', broadcast=True)
        emit('game_state', get_game_state(), broadcast=True)
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
    action = data['action']
    amount = data.get('amount', 0)

    if game.process_action(player_index, action, amount):
        if game.is_betting_round_complete():
            logger.debug(f'Betting round {game.current_betting_round} is complete.')
            active_players_in_hand = [p for p in game.players if not p.folded]

            if len(active_players_in_hand) <= 1:
                winner = active_players_in_hand[0]
                winner.chips += game.pot
                emit('game_message', f'{winner.name} wins ${game.pot} (everyone else folded)', broadcast=True)
                game.end_hand()
                emit('game_state', get_game_state(), broadcast=True)

            elif game.current_betting_round == 3:
                logger.debug('River betting round complete, evaluating hands.')
                winners = game.get_winners()
                if winners:
                    pot_per_winner = game.pot // len(winners)
                    winner_names = ', '.join([w.name for w in winners])
                    winning_hand_rank, winning_hand_kickers = HandEvaluator.evaluate_hand(winners[0].hand, game.community_cards)
                    winning_hand_name = HandEvaluator.get_hand_name(winning_hand_rank)
                    emit('game_message', f'{winner_names} win(s) ${pot_per_winner} each with {winning_hand_name}', broadcast=True)
                    for winner in winners:
                        winner.chips += pot_per_winner
                else:
                    emit('game_message', 'No active players to determine a winner.', broadcast=True)
                game.end_hand()
                emit('game_state', get_game_state(), broadcast=True)

            else:
                logger.debug('Betting round complete, dealing next community card(s).')
                if len(game.community_cards) == 0:
                    game.deal_community_cards(3)
                    emit('game_message', 'Dealing the Flop', broadcast=True)
                elif len(game.community_cards) == 3:
                    game.deal_community_cards(1)
                    emit('game_message', 'Dealing the Turn', broadcast=True)
                elif len(game.community_cards) == 4:
                    game.deal_community_cards(1)
                    emit('game_message', 'Dealing the River', broadcast=True)

                emit('game_state', get_game_state(), broadcast=True)
                if game.current_player_index is not None:
                    next_player = game.players[game.current_player_index]
                    for sid, name in players.items():
                        if name == next_player.name:
                            emit('your_turn', room=sid)
                            break

        else:
            logger.debug('Betting round not complete, moving to next player.')
            emit('game_state', get_game_state(), broadcast=True)
            if game.current_player_index is not None:
                next_player = game.players[game.current_player_index]
                for sid, name in players.items():
                    if name == next_player.name:
                        emit('your_turn', room=sid)
                        break
    else:
        highest_bet = max(p.bet for p in game.players) if game.players else 0
        min_raise = highest_bet + (highest_bet - game.players[player_index].bet)
        if game.current_betting_round == 0 and highest_bet == game.big_blind:
            min_raise = game.big_blind
        emit('game_message', f'Invalid action. Minimum raise is ${min_raise}.')

if __name__ == '__main__':
    socketio.run(app, debug=True)