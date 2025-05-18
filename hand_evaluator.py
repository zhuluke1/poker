from typing import List, Tuple
from card import Card
from collections import Counter

class HandEvaluator:
    # Hand rankings from highest to lowest
    ROYAL_FLUSH = 10
    STRAIGHT_FLUSH = 9
    FOUR_OF_A_KIND = 8
    FULL_HOUSE = 7
    FLUSH = 6
    STRAIGHT = 5
    THREE_OF_A_KIND = 4
    TWO_PAIR = 3
    ONE_PAIR = 2
    HIGH_CARD = 1

    @staticmethod
    def evaluate_hand(hole_cards: List[Card], community_cards: List[Card]) -> Tuple[int, List[int]]:
        """
        Evaluate a poker hand and return its rank and kickers
        Returns: (hand_rank, kickers)
        """
        all_cards = hole_cards + community_cards
        values = [card.value for card in all_cards]
        suits = [card.suit for card in all_cards]
        
        # Check for flush
        flush_cards = HandEvaluator._get_flush_cards(all_cards)
        if flush_cards:
            # Check for straight flush
            straight_flush = HandEvaluator._get_straight_cards(flush_cards)
            if straight_flush:
                # Check for royal flush
                if straight_flush[0].value == 14:
                    return HandEvaluator.ROYAL_FLUSH, [14]
                return HandEvaluator.STRAIGHT_FLUSH, [straight_flush[0].value]
            return HandEvaluator.FLUSH, sorted([card.value for card in flush_cards[:5]], reverse=True)
        
        # Check for straight
        straight = HandEvaluator._get_straight_cards(all_cards)
        if straight:
            return HandEvaluator.STRAIGHT, [straight[0].value]
        
        # Check for other hands
        value_counts = Counter(values)
        counts = value_counts.most_common()
        
        # Four of a kind
        if counts[0][1] == 4:
            kicker = max(v for v in values if v != counts[0][0])
            return HandEvaluator.FOUR_OF_A_KIND, [counts[0][0], kicker]
        
        # Full house
        if counts[0][1] == 3 and counts[1][1] >= 2:
            return HandEvaluator.FULL_HOUSE, [counts[0][0], counts[1][0]]
        
        # Three of a kind
        if counts[0][1] == 3:
            kickers = sorted([v for v in values if v != counts[0][0]], reverse=True)[:2]
            return HandEvaluator.THREE_OF_A_KIND, [counts[0][0]] + kickers
        
        # Two pair
        if counts[0][1] == 2 and counts[1][1] == 2:
            kicker = max(v for v in values if v not in [counts[0][0], counts[1][0]])
            return HandEvaluator.TWO_PAIR, [counts[0][0], counts[1][0], kicker]
        
        # One pair
        if counts[0][1] == 2:
            kickers = sorted([v for v in values if v != counts[0][0]], reverse=True)[:3]
            return HandEvaluator.ONE_PAIR, [counts[0][0]] + kickers
        
        # High card
        return HandEvaluator.HIGH_CARD, sorted(values, reverse=True)[:5]

    @staticmethod
    def _get_flush_cards(cards: List[Card]) -> List[Card]:
        """Get cards that form a flush, if any"""
        suit_counts = Counter(card.suit for card in cards)
        flush_suit = next((suit for suit, count in suit_counts.items() if count >= 5), None)
        if flush_suit:
            return sorted([card for card in cards if card.suit == flush_suit],
                        key=lambda x: x.value, reverse=True)
        return []

    @staticmethod
    def _get_straight_cards(cards: List[Card]) -> List[Card]:
        """Get cards that form a straight, if any"""
        values = sorted(set(card.value for card in cards), reverse=True)
        
        # Check for Ace-low straight (A-5-4-3-2)
        if set([14, 2, 3, 4, 5]).issubset(values):
            return [card for card in cards if card.value in [14, 2, 3, 4, 5]]
        
        # Check for regular straights
        for i in range(len(values) - 4):
            if values[i] - values[i + 4] == 4:
                straight_values = values[i:i + 5]
                return [card for card in cards if card.value in straight_values]
        
        return []

    @staticmethod
    def get_hand_name(rank: int) -> str:
        """Convert hand rank to string name"""
        return {
            HandEvaluator.ROYAL_FLUSH: "Royal Flush",
            HandEvaluator.STRAIGHT_FLUSH: "Straight Flush",
            HandEvaluator.FOUR_OF_A_KIND: "Four of a Kind",
            HandEvaluator.FULL_HOUSE: "Full House",
            HandEvaluator.FLUSH: "Flush",
            HandEvaluator.STRAIGHT: "Straight",
            HandEvaluator.THREE_OF_A_KIND: "Three of a Kind",
            HandEvaluator.TWO_PAIR: "Two Pair",
            HandEvaluator.ONE_PAIR: "One Pair",
            HandEvaluator.HIGH_CARD: "High Card"
        }[rank] 