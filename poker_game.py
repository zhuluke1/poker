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
        self.highest_bet_in_round = 0
        self.is_hand_in_progress = False
        self.actions_taken = 0
        self.last_aggressive_actor_index = None
        self.current_betting_round = 0
        self.first_actor_index = 0

    def start_hand(self):
        """Start a new hand"""
        self.deck.reset()
        self.community_cards = []
        self.pot = 0
        self.actions_taken = 0
        self.last_aggressive_actor_index = None
        self.current_betting_round = 0
        self.highest_bet_in_round = self.big_blind
        for player in self.players:
            player.clear_hand()

        # Post blinds
        if len(self.players) == 2:
            sb_pos = self.dealer_position
            bb_pos = (self.dealer_position + 1) % 2
        else:
            sb_pos = (self.dealer_position + 1) % len(self.players)
            bb_pos = (self.dealer_position + 2) % len(self.players)

        self.players[sb_pos].place_bet(self.small_blind)
        self.players[bb_pos].place_bet(self.big_blind)
        self.pot = self.small_blind + self.big_blind

        # Deal cards
        for player in self.players:
            player.receive_cards(self.deck.deal(2))

        # Set first to act
        if len(self.players) == 2:
            self.current_player_index = sb_pos
            self.first_actor_index = sb_pos
        else:
            self.current_player_index = (bb_pos + 1) % len(self.players)
            self.first_actor_index = (bb_pos + 1) % len(self.players)

        self.is_hand_in_progress = True

    def deal_community_cards(self, count: int):
        """Deal community cards"""
        self.community_cards.extend(self.deck.deal(count))
        self.actions_taken = 0
        self.last_aggressive_actor_index = None
        self.current_betting_round += 1
        self.highest_bet_in_round = 0
        for player in self.players:
            player.bet = 0

        # Set first to act post-flop
        if len(self.players) == 2:
            bb_pos = (self.dealer_position + 1) % 2
            self.current_player_index = bb_pos
            self.first_actor_index = bb_pos
        else:
            self.current_player_index = (self.dealer_position + 1) % len(self.players)
            self.first_actor_index = self.current_player_index
            while self.players[self.current_player_index].folded or self.players[self.current_player_index].is_all_in:
                self.current_player_index = (self.current_player_index + 1) % len(self.players)
                self.first_actor_index = self.current_player_index

    def next_player(self) -> Optional[Player]:
        """Move to the next active player"""
        self.actions_taken += 1
        start_index = self.current_player_index
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            player = self.players[self.current_player_index]

            if not player.folded and not player.is_all_in:
                return player

            if self.current_player_index == start_index:
                return None

    def process_action(self, player_index: int, action: str, amount: int = 0) -> bool:
        """Process a player's action (fold, call, check, raise)"""
        player = self.players[player_index]
        if player.folded or player.is_all_in or player_index != self.current_player_index:
            return False

        highest_bet = max(p.bet for p in self.players) if self.players else 0

        if action == "fold":
            player.fold()
            self.next_player()
            return True
        elif action == "check":
            if player.bet == highest_bet:
                self.next_player()
                return True
            return False
        elif action == "call":
            amount_to_call = highest_bet - player.bet
            if amount_to_call > player.chips:
                amount_to_call = player.chips
                player.is_all_in = True
            player.place_bet(amount_to_call)
            self.pot += amount_to_call
            self.next_player()
            return True
        elif action == "raise":
            min_raise = highest_bet + (highest_bet - player.bet)
            if self.current_betting_round == 0 and highest_bet == self.big_blind:
                min_raise = self.big_blind
            if amount < min_raise:
                return False
            if amount > player.chips + player.bet:
                return False
            bet_increase = amount - player.bet
            player.place_bet(bet_increase)
            self.pot += bet_increase
            self.highest_bet_in_round = player.bet
            self.last_aggressive_actor_index = player_index
            self.next_player()
            return True
        return False

    def is_betting_round_complete(self) -> bool:
        """Check if the current betting round is complete"""
        active_players = [p for p in self.players if not p.folded and not p.is_all_in]
        if len(active_players) <= 1:
            return True

        highest_bet = max(p.bet for p in self.players) if self.players else 0
        all_matched_or_all_in = all(p.bet == highest_bet or p.is_all_in for p in active_players)

        if not all_matched_or_all_in:
            return False

        if self.last_aggressive_actor_index is None:
            return self.actions_taken >= len(active_players)
        else:
            return self.current_player_index == self.last_aggressive_actor_index

    def end_hand(self):
        """End the current hand and move the dealer button"""
        self.dealer_position = (self.dealer_position + 1) % len(self.players)
        self.is_hand_in_progress = False
        self.actions_taken = 0
        self.last_aggressive_actor_index = None
        self.current_betting_round = 0
        self.highest_bet_in_round = 0

    def get_active_players(self) -> List[Player]:
        """Get list of players who haven't folded"""
        return [p for p in self.players if not p.folded]

    def evaluate_hands(self) -> List[Tuple[Player, int, List[int]]]:
        """Evaluate all active players' hands and return sorted list of (player, rank, kickers)"""
        active_players = self.get_active_players()
        if not active_players:
            return []

        evaluated_hands = []
        for player in active_players:
            rank, kickers = HandEvaluator.evaluate_hand(player.hand, self.community_cards)
            evaluated_hands.append((player, rank, kickers))

        return sorted(evaluated_hands, key=lambda x: (x[1], x[2]), reverse=True)

    def get_winners(self) -> List[Player]:
        """Get list of winning players (handles ties)"""
        evaluated_hands = self.evaluate_hands()
        if not evaluated_hands:
            return []

        highest_rank = evaluated_hands[0][1]
        highest_kickers = evaluated_hands[0][2]

        return [player for player, rank, kickers in evaluated_hands
                if rank == highest_rank and kickers == highest_kickers]