from typing import List
from card import Card

class Player:
    def __init__(self, name: str, chips: int = 1000):
        self.name = name
        self.chips = chips
        self.hand: List[Card] = []
        self.bet = 0
        self.folded = False
        self.is_all_in = False
    
    def receive_cards(self, cards: List[Card]):
        """Receive cards dealt to the player"""
        self.hand = cards
    
    def place_bet(self, amount: int) -> int:
        """Place a bet and return the actual amount bet"""
        if amount > self.chips:
            amount = self.chips
            self.is_all_in = True
        
        self.chips -= amount
        self.bet += amount
        return amount
    
    def fold(self):
        """Fold the current hand"""
        self.folded = True
    
    def clear_hand(self):
        """Clear the player's hand and reset betting state"""
        self.hand = []
        self.bet = 0
        self.folded = False
        self.is_all_in = False
    
    def __str__(self):
        return f"{self.name} (Chips: {self.chips})" 