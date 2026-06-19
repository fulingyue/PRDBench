"""SQLite database manager for battle data recording."""

import sqlite3
import time
import json
import os


class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'game_data.db')
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                player1_id INTEGER,
                player2_id INTEGER,
                start_time REAL,
                end_time REAL,
                total_moves INTEGER DEFAULT 0,
                winner_id INTEGER,
                finished INTEGER DEFAULT 0,
                key_moves TEXT DEFAULT '[]',
                FOREIGN KEY (player1_id) REFERENCES players(player_id),
                FOREIGN KEY (player2_id) REFERENCES players(player_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS move_cache (
                cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER,
                move_number INTEGER,
                player_id INTEGER,
                position TEXT,
                timestamp REAL,
                FOREIGN KEY (game_id) REFERENCES games(game_id)
            )
        ''')
        self.conn.commit()

    def add_player(self, name):
        try:
            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO players (name) VALUES (?)', (name,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def delete_player(self, name):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM players WHERE name = ?', (name,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_all_players(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT player_id, name FROM players ORDER BY player_id')
        return cursor.fetchall()

    def create_game_record(self, game_type, player1_id, player2_id, start_time=None):
        if start_time is None:
            start_time = time.time()
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO games (game_type, player1_id, player2_id, start_time)
            VALUES (?, ?, ?, ?)
        ''', (game_type, player1_id, player2_id, start_time))
        self.conn.commit()
        return cursor.lastrowid

    def finish_game(self, game_id, winner_id, end_time, total_moves, key_moves):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE games SET winner_id = ?, end_time = ?, total_moves = ?,
            finished = 1, key_moves = ? WHERE game_id = ?
        ''', (winner_id, end_time, total_moves, json.dumps(key_moves), game_id))
        self.conn.commit()

    def cache_moves(self, game_id, moves):
        cursor = self.conn.cursor()
        for move in moves:
            cursor.execute('''
                INSERT INTO move_cache (game_id, move_number, player_id, position, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (game_id, move['move_number'], move['player_id'], move['position'], move['timestamp']))
        self.conn.commit()

    def get_cached_game(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM games WHERE finished = 0 ORDER BY game_id DESC LIMIT 1')
        return cursor.fetchone()

    def get_cached_moves(self, game_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM move_cache WHERE game_id = ? ORDER BY move_number', (game_id,))
        return cursor.fetchall()

    def get_game_history(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT g.*, p1.name as player1_name, p2.name as player2_name,
                   pw.name as winner_name
            FROM games g
            LEFT JOIN players p1 ON g.player1_id = p1.player_id
            LEFT JOIN players p2 ON g.player2_id = p2.player_id
            LEFT JOIN players pw ON g.winner_id = pw.player_id
            WHERE g.finished = 1
            ORDER BY g.start_time DESC
        ''')
        return cursor.fetchall()

    def clear_all_data(self):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM move_cache')
        cursor.execute('DELETE FROM games')
        cursor.execute('DELETE FROM players')
        self.conn.commit()

    def close(self):
        self.conn.close()
