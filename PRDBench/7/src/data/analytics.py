"""Data analysis center for battle statistics."""

import time
import csv
import os


class AnalyticsCenter:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_7day_frequency_ranking(self):
        week_ago = time.time() - 7 * 24 * 60 * 60
        players = self.db.get_all_players()
        rankings = []
        for player in players:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM games
                WHERE (player1_id = ? OR player2_id = ?)
                AND finished = 1
                AND start_time > ?
            ''', (player['player_id'], player['player_id'], week_ago))
            count = cursor.fetchone()[0]
            rankings.append((player['name'], count))
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    def get_win_rate(self, player_id, game_type=None, days=None):
        cursor = self.db.conn.cursor()
        query = '''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN winner_id = ? THEN 1 ELSE 0 END) as wins
            FROM games
            WHERE (player1_id = ? OR player2_id = ?)
            AND finished = 1
        '''
        params = [player_id, player_id, player_id]
        if game_type:
            query += ' AND game_type = ?'
            params.append(game_type)
        if days:
            cutoff = time.time() - days * 24 * 60 * 60
            query += ' AND start_time > ?'
            params.append(cutoff)
        cursor.execute(query, params)
        row = cursor.fetchone()
        total = row[0]
        wins = row[1]
        if total == 0:
            return 0.0
        return round(wins / total * 100, 2)

    def get_player_stats(self, player_id):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM games
            WHERE (player1_id = ? OR player2_id = ?) AND finished = 1
        ''', (player_id, player_id))
        total = cursor.fetchone()[0]
        win_rate = self.get_win_rate(player_id)
        return {'total_games': total, 'win_rate': win_rate}

    def get_opening_heatmap(self, game_type='gomoku'):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT key_moves FROM games
            WHERE game_type = ? AND finished = 1
        ''', (game_type,))
        import json
        heatmap = {}
        for row in cursor.fetchall():
            moves = json.loads(row['key_moves']) if row['key_moves'] else []
            if moves:
                first_move = moves[0] if isinstance(moves[0], str) else str(moves[0])
                heatmap[first_move] = heatmap.get(first_move, 0) + 1
        return heatmap

    def generate_ascii_heatmap(self, heatmap, board_size=15):
        if not heatmap:
            return "No data available for heatmap."
        max_count = max(heatmap.values()) if heatmap else 1
        levels = [' ', '.', 'o', 'O', '#']
        lines = []
        lines.append("   " + " ".join(chr(65 + i) for i in range(board_size)))
        for row in range(1, board_size + 1):
            line = f"{row:2d} "
            cells = []
            for col in range(board_size):
                pos = f"{chr(65 + col)}{row}"
                count = heatmap.get(pos, 0)
                if count == 0:
                    cells.append('+')
                else:
                    idx = min(int(count / max_count * (len(levels) - 1)), len(levels) - 1)
                    cells.append(levels[idx])
            line += " ".join(cells)
            lines.append(line)
        return "\n".join(lines)

    def export_to_csv(self, filepath='export.csv'):
        players = self.db.get_all_players()
        data = []
        for p in players:
            stats = self.get_player_stats(p['player_id'])
            data.append({
                'player': p['name'],
                'total_games': stats['total_games'],
                'win_rate': f"{stats['win_rate']:.2f}"
            })
        data.sort(key=lambda x: int(x['total_games']), reverse=True)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['player', 'total_games', 'win_rate'])
            writer.writeheader()
            writer.writerows(data)
        return filepath
