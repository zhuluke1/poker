from typing import List, Optional, Tuple
from card import Card, Deck
from player import Player
from hand_evaluator import HandEvaluator

class PokerGame:
    def __init__(self, players: List[Player], small_blind: int = 5, big_blind: int = 10):
        self.players = players
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.dealer_position = 0
        self.current_player_index = 0
        self.minimum_bet = big_blind
        self.is_hand_in_progress = False
    
    def start_hand(self):
        """Start a new hand"""
        # Reset game state
        self.deck.reset()
        self.community_cards = []
        self.pot = 0
        for player in self.players:
            player.clear_hand()
        
        # Post blinds
        if len(self.players) == 2:  # Heads-up play
            # In heads-up, dealer is small blind and acts first
            sb_pos = self.dealer_position
            bb_pos = (self.dealer_position + 1) % 2
        else:  # Regular play
            sb_pos = (self.dealer_position + 1) % len(self.players)
            bb_pos = (self.dealer_position + 2) % len(self.players)
        
        self.players[sb_pos].place_bet(self.small_blind)
        self.players[bb_pos].place_bet(self.big_blind)
        self.pot = self.small_blind + self.big_blind
        
        # Deal cards
        for player in self.players:
            player.receive_cards(self.deck.deal(2))
        
        # Set first to act
        if len(self.players) == 2:  # Heads-up play
            # Small blind (dealer) acts first pre-flop
            self.current_player_index = sb_pos
        else:  # Regular play
            # First to act is after big blind
            self.current_player_index = (bb_pos + 1) % len(self.players)
        
        self.is_hand_in_progress = True
    
    def deal_community_cards(self, count: int):
        """Deal community cards"""
        self.community_cards.extend(self.deck.deal(count))
    
    def next_player(self) -> Optional[Player]:
        """Move to the next active player"""
        start_index = self.current_player_index
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            player = self.players[self.current_player_index]
            
            if not player.folded and not player.is_all_in:
                return player
            
            if self.current_player_index == start_index:
                return None
    
    def is_hand_complete(self) -> bool:
        """Check if the current betting round is complete"""
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) <= 1:
            return True
            
        # Check if all active players have matched the highest bet
        highest_bet = max(p.bet for p in self.players)
        
        # In heads-up play, we need to ensure both players have acted
        if len(self.players) == 2:
            # If we're pre-flop, both players must have acted
            if len(self.community_cards) == 0:
                # Small blind must have acted (either called or raised)
                sb_pos = self.dealer_position
                if self.players[sb_pos].bet < self.big_blind:
                    return False
                # Big blind must have acted if small blind raised
                bb_pos = (self.dealer_position + 1) % 2
                if self.players[sb_pos].bet > self.big_blind and self.players[bb_pos].bet < self.players[sb_pos].bet:
                    return False
            # Post-flop, just check if bets are matched
            return all(p.bet == highest_bet or p.is_all_in for p in active_players)
        else:
            # Regular play: check if all active players have matched the highest bet
            return all(p.bet == highest_bet or p.is_all_in for p in active_players)
    
    def end_hand(self):
        """End the current hand and move the dealer button"""
        self.dealer_position = (self.dealer_position + 1) % len(self.players)
        self.is_hand_in_progress = False
    
    def get_active_players(self) -> List[Player]:
        """Get list of players who haven't folded"""
        return [p for p in self.players if not p.folded]
    
    def evaluate_hands(self) -> List[Tuple[Player, int, List[int]]]:
        """Evaluate all active players' hands and return sorted list of (player, rank, kickers)"""
        active_players = self.get_active_players()
        if not active_players:
            return []
            
        # Evaluate each player's hand
        evaluated_hands = []
        for player in active_players:
            rank, kickers = HandEvaluator.evaluate_hand(player.hand, self.community_cards)
            evaluated_hands.append((player, rank, kickers))
        
        # Sort by rank (descending) and then by kickers (descending)
        return sorted(evaluated_hands, key=lambda x: (x[1], x[2]), reverse=True)
    
    def get_winners(self) -> List[Player]:
        """Get list of winning players (handles ties)"""
        evaluated_hands = self.evaluate_hands()
        if not evaluated_hands:
            return []
            
        # Get the highest rank and kickers
        highest_rank = evaluated_hands[0][1]
        highest_kickers = evaluated_hands[0][2]
        
        # Return all players with the same highest rank and kickers
        return [player for player, rank, kickers in evaluated_hands 
                if rank == highest_rank and kickers == highest_kickers] 