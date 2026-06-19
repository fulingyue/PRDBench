#!/usr/bin/env python3
"""Command Line Board Game Battle and Data Statistics System."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.database import DatabaseManager
from data.analytics import AnalyticsCenter
from game.player import PlayerManager, Player
from game.gomoku import GomokuGame
from utils.config import ConfigManager


def safe_input(prompt=""):
    try:
        return input(prompt).strip()
    except EOFError:
        return None


def main():
    db = DatabaseManager()
    player_mgr = PlayerManager(db)
    config = ConfigManager()
    analytics = AnalyticsCenter(db)

    while True:
        print("\n===== Board Game Battle System =====")
        print("1. Start New Match")
        print("2. Continue Match")
        print("3. View Historical Data")
        print("4. Data Analysis Center")
        print("5. System Configuration")
        print("6. Exit System")

        choice = safe_input("Please select (1-6): ")
        if choice is None:
            break

        if choice == '1':
            start_new_match(db, player_mgr, config)
        elif choice == '2':
            continue_match(db, player_mgr, config)
        elif choice == '3':
            view_history(db)
        elif choice == '4':
            data_analysis_center(analytics, db)
        elif choice == '5':
            system_config(db, player_mgr, config)
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid input, please select a number between 1-6.")

    db.close()


def _resolve_player(player_mgr, players, val):
    if val is None:
        return None
    # Try index first
    try:
        idx = int(val) - 1
        if 0 <= idx < len(players):
            return players[idx]
    except (ValueError, TypeError):
        pass
    # Try name match
    p = player_mgr.get_player_by_name(val)
    if p:
        return p
    # Auto-create
    p = player_mgr.create_player(val)
    return p


def start_new_match(db, player_mgr, config):
    print("\nSelect game type:")
    print("1. Gomoku")
    print("2. Chinese Chess")
    choice = safe_input("Select (1-2): ")
    if choice not in ('1', '2'):
        print("Invalid selection.")
        return

    players = player_mgr.get_all_players()

    if players:
        print("\nAvailable players:")
        for i, p in enumerate(players):
            print(f"  {i + 1}. {p.name}")
        p1_input = safe_input("Select Player 1 (number or name): ")
        p2_input = safe_input("Select Player 2 (number or name): ")
    else:
        p1_input = safe_input("Enter Player 1 name: ")
        p2_input = safe_input("Enter Player 2 name: ")

    p1 = _resolve_player(player_mgr, players, p1_input)
    p2 = _resolve_player(player_mgr, players, p2_input)

    if p1 is None or p2 is None:
        print("Invalid player selection.")
        return

    if p1.player_id == p2.player_id:
        print("Players must be different.")
        return

    if choice == '1':
        game = GomokuGame(p1, p2, db, config)
        game.start()
    else:
        from game.xiangqi import XiangqiGame
        game = XiangqiGame(p1, p2, db, config)
        game.start()


def continue_match(db, player_mgr, config):
    cached = db.get_cached_game()
    if cached is None:
        print("No unfinished match found.")
        return

    moves = db.get_cached_moves(cached['game_id'])
    p1 = player_mgr.get_player_by_id(cached['player1_id']) if hasattr(player_mgr, 'get_player_by_id') else None
    p2 = player_mgr.get_player_by_id(cached['player2_id']) if hasattr(player_mgr, 'get_player_by_id') else None

    if p1 is None or p2 is None:
        players = player_mgr.get_all_players()
        p1_match = [p for p in players if p.player_id == cached['player1_id']]
        p2_match = [p for p in players if p.player_id == cached['player2_id']]
        p1 = p1_match[0] if p1_match else Player(cached['player1_id'], "Player1")
        p2 = p2_match[0] if p2_match else Player(cached['player2_id'], "Player2")

    game_type = cached['game_type']
    move_data = [{'move_number': m['move_number'], 'player_id': m['player_id'],
                  'position': m['position'], 'timestamp': m['timestamp']} for m in moves]

    if game_type == 'gomoku':
        game = GomokuGame(p1, p2, db, config)
        game.game_id = cached['game_id']
        game.resume(move_data)
    else:
        from game.xiangqi import XiangqiGame
        game = XiangqiGame(p1, p2, db, config)
        game.game_id = cached['game_id']
        print("Resuming Chinese Chess match...")
        game.board.display(config.get_board_style())


def view_history(db):
    history = db.get_game_history()
    if not history:
        print("\nNo match records found.")
        return
    print(f"\n===== Match History ({len(history)} records) =====")
    for g in history:
        game_type = g['game_type'].capitalize()
        p1 = g['player1_name'] or 'Unknown'
        p2 = g['player2_name'] or 'Unknown'
        winner = g['winner_name'] or 'Draw'
        moves = g['total_moves']
        print(f"  ID:{g['game_id']} | {game_type} | {p1} vs {p2} | "
              f"Winner: {winner} | Moves: {moves}")


def data_analysis_center(analytics, db):
    while True:
        print("\n===== Data Analysis Center =====")
        print("1. 7-Day Match Frequency Ranking")
        print("2. Win Rate Statistics")
        print("3. Opening Move Heatmap")
        print("4. Export Data to CSV")
        print("5. Back")

        choice = safe_input("Select (1-5): ")
        if choice is None or choice == '5':
            return

        if choice == '1':
            rankings = analytics.get_7day_frequency_ranking()
            print("\n--- 7-Day Match Frequency Ranking ---")
            if not rankings:
                print("No data available.")
            for i, (name, count) in enumerate(rankings):
                print(f"  {i + 1}. {name}: {count} matches")

        elif choice == '2':
            players = db.get_all_players()
            if not players:
                print("No players found.")
                continue
            print("\n--- Win Rate Statistics ---")
            for p in players:
                overall = analytics.get_win_rate(p['player_id'])
                gomoku = analytics.get_win_rate(p['player_id'], 'gomoku')
                xiangqi = analytics.get_win_rate(p['player_id'], 'xiangqi')
                print(f"  {p['name']}: Overall={overall}%, Gomoku={gomoku}%, Chess={xiangqi}%")

        elif choice == '3':
            heatmap = analytics.get_opening_heatmap()
            print("\n--- Opening Move Heatmap (Gomoku) ---")
            print(analytics.generate_ascii_heatmap(heatmap))

        elif choice == '4':
            path = analytics.export_to_csv()
            print(f"Data exported to {path}")

        else:
            print("Invalid input.")


def system_config(db, player_mgr, config):
    while True:
        print("\n===== System Configuration =====")
        print("1. Player Info Management")
        print("2. Board Display Style Switch")
        print("3. Clear All Data")
        print("4. Back")

        choice = safe_input("Select (1-4): ")
        if choice is None or choice == '4':
            return

        if choice == '1':
            player_management(player_mgr)
        elif choice == '2':
            board_style_switch(config)
        elif choice == '3':
            confirm = safe_input("Are you sure you want to clear all data? (yes/y): ")
            if confirm and confirm.lower() in ('yes', 'y'):
                db.clear_all_data()
                print("All data cleared.")
            else:
                print("Cancelled.")
        else:
            print("Invalid input.")


def player_management(player_mgr):
    while True:
        print("\n--- Player Info Management ---")
        print("1. Create Player")
        print("2. Delete Player")
        print("3. Back")

        choice = safe_input("Select (1-3): ")
        if choice is None or choice == '3':
            return

        if choice == '1':
            name = safe_input("Enter player name: ")
            if not name:
                print("Name cannot be empty.")
                continue
            result = player_mgr.create_player(name)
            if result:
                print(f"Player '{name}' created successfully! (ID: {result.player_id})")
            else:
                print("Failed to create player. Name may already exist or limit reached (max 10).")

        elif choice == '2':
            players = player_mgr.get_all_players()
            if not players:
                print("No players to delete.")
                continue
            print("Players:")
            for i, p in enumerate(players):
                print(f"  {i + 1}. {p.name}")
            idx = safe_input("Select player to delete (number): ")
            try:
                p = players[int(idx) - 1]
                confirm = safe_input(f"Delete '{p.name}'? (yes/y): ")
                if confirm and confirm.lower() in ('yes', 'y'):
                    player_mgr.delete_player(p.name)
                    print(f"Player '{p.name}' deleted.")
                else:
                    print("Cancelled.")
            except (ValueError, IndexError, TypeError):
                print("Invalid selection.")

        else:
            print("Invalid input.")


def board_style_switch(config):
    print("\n--- Board Display Style ---")
    print("1. Compact")
    print("2. Standard")
    print("3. Expanded")
    current = config.get_board_style()
    print(f"Current style: {current}")

    choice = safe_input("Select style (1-3): ")
    styles = {'1': 'compact', '2': 'standard', '3': 'expanded'}
    if choice in styles:
        config.set_board_style(styles[choice])
        print(f"Style changed to {styles[choice]}.")
    else:
        print("Invalid selection.")


if __name__ == '__main__':
    main()
