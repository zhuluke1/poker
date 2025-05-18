from enum import Enum
import random

class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

class Card:
    def __init__(self, suit: Suit, value: int):
        self.suit = suit
        self.value = value
        
    def __str__(self):
        value_str = {
            11: 'J',
            12: 'Q',
            13: 'K',
            14: 'A'
        }.get(self.value, str(self.value))
        return f"{value_str}{self.suit.value}"
    
    def __repr__(self):
        return self.__str__()

class Deck:
    def __init__(self):
        self.cards = []
        self.reset()
    
    def reset(self):
        """Reset the deck to a full set of cards"""
        self.cards = [
            Card(suit, value)
            for suit in Suit
            for value in range(2, 15)  # 2-14 (Ace is 14)
        ]
        self.shuffle()
    
    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)
    
    def deal(self, num_cards: int = 1) -> list[Card]:
        """Deal a specified number of cards from the deck"""
        if len(self.cards) < num_cards:
            raise ValueError("Not enough cards in deck")
        return [self.cards.pop() for _ in range(num_cards)] 