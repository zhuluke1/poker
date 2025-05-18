from poker_game import PokerGame
from player import Player
from hand_evaluator import HandEvaluator

def print_game_state(game):
    print("\n" + "="*50)
    print(f"Pot: ${game.pot}")
    print("\nCommunity Cards:", " ".join(str(card) for card in game.community_cards))
    print("\nPlayers:")
    for i, player in enumerate(game.players):
        status = " (Dealer)" if i == game.dealer_position else ""
        status += " (Current)" if i == game.current_player_index else ""
        print(f"{player.name}{status}: ${player.chips} | Bet: ${player.bet}")
        if player.hand:
            print(f"  Hand: {' '.join(str(card) for card in player.hand)}")
    print("="*50 + "\n")

def get_player_action(player, min_bet):
    while True:
        print(f"\n{player.name}'s turn. Current bet: ${min_bet}")
        print("1. Fold")
        print("2. Call")
        print("3. Raise")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == "1":
            return "fold", 0
        elif choice == "2":
            return "call", min_bet - player.bet
        elif choice == "3":
            while True:
                try:
                    amount = int(input(f"Enter raise amount (minimum ${min_bet * 2}): "))
                    if amount >= min_bet * 2:
                        return "raise", amount
                    print("Invalid raise amount!")
                except ValueError:
                    print("Please enter a valid number!")

def main():
    # Create players
    num_players = int(input("Enter number of players (2-6): "))
    players = []
    for i in range(num_players):
        name = input(f"Enter name for player {i+1}: ")
        players.append(Player(name))
    
    # Create game
    game = PokerGame(players)
    
    while True:
        game.start_hand()
        print_game_state(game)
        
        # Pre-flop betting
        while not game.is_hand_complete():
            current_player = game.players[game.current_player_index]
            if not current_player.folded and not current_player.is_all_in:
                action, amount = get_player_action(current_player, game.minimum_bet)
                
                if action == "fold":
                    current_player.fold()
                else:
                    current_player.place_bet(amount)
                    game.pot += amount
                    if amount > game.minimum_bet:
                        game.minimum_bet = amount
            
            game.next_player()
            print_game_state(game)
        
        # Deal flop
        if len(game.get_active_players()) > 1:
            game.deal_community_cards(3)
            print_game_state(game)
            
            # Reset betting for flop
            game.minimum_bet = game.big_blind
            for player in game.players:
                player.bet = 0
            
            # Flop betting
            while not game.is_hand_complete():
                current_player = game.players[game.current_player_index]
                if not current_player.folded and not current_player.is_all_in:
                    action, amount = get_player_action(current_player, game.minimum_bet)
                    
                    if action == "fold":
                        current_player.fold()
                    else:
                        current_player.place_bet(amount)
                        game.pot += amount
                        if amount > game.minimum_bet:
                            game.minimum_bet = amount
                
                game.next_player()
                print_game_state(game)
        
        # Deal turn
        if len(game.get_active_players()) > 1:
            game.deal_community_cards(1)
            print_game_state(game)
            
            # Reset betting for turn
            game.minimum_bet = game.big_blind
            for player in game.players:
                player.bet = 0
            
            # Turn betting
            while not game.is_hand_complete():
                current_player = game.players[game.current_player_index]
                if not current_player.folded and not current_player.is_all_in:
                    action, amount = get_player_action(current_player, game.minimum_bet)
                    
                    if action == "fold":
                        current_player.fold()
                    else:
                        current_player.place_bet(amount)
                        game.pot += amount
                        if amount > game.minimum_bet:
                            game.minimum_bet = amount
                
                game.next_player()
                print_game_state(game)
        
        # Deal river
        if len(game.get_active_players()) > 1:
            game.deal_community_cards(1)
            print_game_state(game)
            
            # Reset betting for river
            game.minimum_bet = game.big_blind
            for player in game.players:
                player.bet = 0
            
            # River betting
            while not game.is_hand_complete():
                current_player = game.players[game.current_player_index]
                if not current_player.folded and not current_player.is_all_in:
                    action, amount = get_player_action(current_player, game.minimum_bet)
                    
                    if action == "fold":
                        current_player.fold()
                    else:
                        current_player.place_bet(amount)
                        game.pot += amount
                        if amount > game.minimum_bet:
                            game.minimum_bet = amount
                
                game.next_player()
                print_game_state(game)
        
        # Determine winner(s)
        active_players = game.get_active_players()
        if len(active_players) == 1:
            winner = active_players[0]
            winner.chips += game.pot
            print(f"\n{winner.name} wins ${game.pot}!")
        else:
            # Showdown
            print("\nShowdown!")
            winners = game.get_winners()
            pot_per_winner = game.pot // len(winners)
            
            for player in winners:
                player.chips += pot_per_winner
                rank, kickers = HandEvaluator.evaluate_hand(player.hand, game.community_cards)
                hand_name = HandEvaluator.get_hand_name(rank)
                print(f"{player.name} wins ${pot_per_winner} with {hand_name}")
        
        game.end_hand()
        
        # Ask to play another hand
        if input("\nPlay another hand? (y/n): ").lower() != 'y':
            break

if __name__ == "__main__":
    main() 