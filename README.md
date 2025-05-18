# Texas Hold'em Poker Game

A simple command-line implementation of Texas Hold'em Poker.

## Features

- Support for 2-6 players
- Full Texas Hold'em rules implementation
- Betting rounds (pre-flop, flop, turn, river)
- Blind system
- Player chip management

## Requirements

- Python 3.7+
- Required packages (install using `pip install -r requirements.txt`):
  - pygame
  - numpy

## How to Run

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the game:
   ```
   python main.py
   ```

## How to Play

1. Enter the number of players (2-6)
2. Enter each player's name
3. The game will automatically:
   - Deal cards to each player
   - Post blinds
   - Handle betting rounds
   - Deal community cards
   - Manage the pot

4. For each turn, you can:
   - Fold (1)
   - Call (2)
   - Raise (3)

5. After each hand, you can choose to play another hand or quit

## Game Rules

- Small blind and big blind are posted automatically
- Minimum raise is 2x the current bet
- All players start with 1000 chips
- Standard Texas Hold'em betting rules apply

## Note

This is a simplified version of Texas Hold'em. The hand evaluation system is not implemented, so in case of a showdown, the pot is awarded to the last player standing.