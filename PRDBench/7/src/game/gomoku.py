"""Gomoku (Five in a Row) game module."""

import time
import json


class GomokuBoard:
    SIZE = 15

    def __init__(self):
        self.grid = [[None for _ in range(self.SIZE)] for _ in range(self.SIZE)]

    def place_piece(self, row, col, piece):
        self.grid[row][col] = piece

    def remove_piece(self, row, col):
        self.grid[row][col] = None

    def get_piece(self, row, col):
        if 0 <= row < self.SIZE and 0 <= col < self.SIZE:
            return self.grid[row][col]
        return None

    def display(self, style='standard'):
        spacing = {'compact': '', 'standard': ' ', 'expanded': '  '}
        sep = spacing.get(style, ' ')
        header = "   " + sep.join(chr(65 + i) for i in range(self.SIZE))
        print(header)
        for row in range(self.SIZE):
            line = f"{row + 1:2d} "
            cells = []
            for col in range(self.SIZE):
                piece = self.grid[row][col]
                if piece is None:
                    cells.append('+')
                elif piece == '\u25cf':
                    cells.append('\u25cf')
                elif piece == '\u25cb':
                    cells.append('\u25cb')
                else:
                    cells.append('+')
            line += sep.join(cells)
            print(line)


class GomokuGame:
    PIECES = ['\u25cf', '\u25cb']  # Black, White

    def __init__(self, player1, player2, db_manager, config_manager):
        self.players = [player1, player2]
        self.board = GomokuBoard()
        self.db = db_manager
        self.config = config_manager
        self.current_turn = 0  # 0 = black (player1), 1 = white (player2)
        self.moves = []
        self.game_id = None
        self.can_undo = False
        self.last_move = None
        self.move_count = 0
        self.game_over = False

    def _parse_position(self, pos_str):
        pos_str = pos_str.strip().upper()
        if len(pos_str) < 2:
            return None
        col_char = pos_str[0]
        if not col_char.isalpha():
            return None
        col = ord(col_char) - ord('A')
        try:
            row = int(pos_str[1:]) - 1
        except ValueError:
            return None
        if 0 <= row < self.board.SIZE and 0 <= col < self.board.SIZE:
            return (row, col)
        return None

    def _is_valid_move(self, row, col):
        if not (0 <= row < self.board.SIZE and 0 <= col < self.board.SIZE):
            return False
        return self.board.grid[row][col] is None

    def _check_win(self, row, col):
        piece = self.board.grid[row][col]
        if piece is None:
            return False
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            for sign in [1, -1]:
                r, c = row + dr * sign, col + dc * sign
                while 0 <= r < self.board.SIZE and 0 <= c < self.board.SIZE and self.board.grid[r][c] == piece:
                    count += 1
                    r += dr * sign
                    c += dc * sign
            if count >= 5:
                return True
        return False

    def _check_four_warning(self, row, col):
        piece = self.board.grid[row][col]
        if piece is None:
            return False
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            for sign in [1, -1]:
                r, c = row + dr * sign, col + dc * sign
                while 0 <= r < self.board.SIZE and 0 <= c < self.board.SIZE and self.board.grid[r][c] == piece:
                    count += 1
                    r += dr * sign
                    c += dc * sign
            if count >= 4:
                return True
        return False

    def _cache_moves_if_needed(self):
        if self.move_count > 0 and self.move_count % 5 == 0:
            uncached = self.moves[-5:]
            cache_data = []
            for m in uncached:
                cache_data.append({
                    'move_number': m['move_number'],
                    'player_id': m['player_id'],
                    'position': m['position'],
                    'timestamp': m['timestamp']
                })
            self.db.cache_moves(self.game_id, cache_data)

    def start(self):
        self.game_id = self.db.create_game_record(
            'gomoku',
            self.players[0].player_id,
            self.players[1].player_id,
            time.time()
        )
        print(f"\n=== Gomoku Match Started ===")
        print(f"Black (\u25cf): {self.players[0].name}")
        print(f"White (\u25cb): {self.players[1].name}")
        print(f"Enter coordinates like 'H8', or 'undo'/'resign'\n")

        self.board.display(self.config.get_board_style())

        while not self.game_over:
            current_player = self.players[self.current_turn]
            piece = self.PIECES[self.current_turn]
            color_name = "Black" if self.current_turn == 0 else "White"

            try:
                cmd = input(f"{color_name} ({current_player.name}) move: ").strip()
            except EOFError:
                self._save_and_exit()
                return

            if not cmd:
                print("Invalid input, please enter a coordinate (e.g., H8), 'undo', or 'resign'.")
                continue

            if cmd.lower() in ('resign', 'surrender'):
                winner = self.players[1 - self.current_turn]
                print(f"\n{current_player.name} surrendered!")
                print(f"Winner: {winner.name}!")
                self.db.finish_game(
                    self.game_id, winner.player_id, time.time(),
                    self.move_count,
                    [m['position'] for m in self.moves[:5]]
                )
                self.game_over = True
                return

            if cmd.lower() == 'undo':
                if self.can_undo and self.last_move:
                    lr, lc = self.last_move
                    self.board.remove_piece(lr, lc)
                    self.moves.pop()
                    self.move_count -= 1
                    self.current_turn = 1 - self.current_turn
                    self.can_undo = False
                    self.last_move = None
                    print("Undo successful!")
                    self.board.display(self.config.get_board_style())
                else:
                    print("Cannot undo: no move to undo or already undone once.")
                continue

            pos = self._parse_position(cmd)
            if pos is None:
                print("Invalid coordinate format. Please use format like 'H8'.")
                continue

            row, col = pos
            if not self._is_valid_move(row, col):
                print("Invalid move: position is already occupied or out of bounds.")
                continue

            self.board.place_piece(row, col, piece)
            self.move_count += 1
            self.moves.append({
                'move_number': self.move_count,
                'player_id': current_player.player_id,
                'position': cmd.upper(),
                'timestamp': time.time()
            })
            self.last_move = (row, col)
            self.can_undo = True

            self._cache_moves_if_needed()
            self.board.display(self.config.get_board_style())

            if self._check_win(row, col):
                print(f"\nCongratulations! {current_player.name} ({color_name}) wins!")
                self.db.finish_game(
                    self.game_id, current_player.player_id, time.time(),
                    self.move_count,
                    [m['position'] for m in self.moves[:5]]
                )
                self.game_over = True
                return

            if self._check_four_warning(row, col):
                print(f"Warning: {color_name} has four in a row!")

            self.current_turn = 1 - self.current_turn

    def _save_and_exit(self):
        if self.game_id and not self.game_over:
            uncached = self.moves[-(self.move_count % 5):] if self.move_count % 5 != 0 else []
            if uncached:
                cache_data = [{
                    'move_number': m['move_number'],
                    'player_id': m['player_id'],
                    'position': m['position'],
                    'timestamp': m['timestamp']
                } for m in uncached]
                self.db.cache_moves(self.game_id, cache_data)

    def resume(self, cached_moves):
        print(f"\n=== Resuming Gomoku Match ===")
        print(f"Black (\u25cf): {self.players[0].name}")
        print(f"White (\u25cb): {self.players[1].name}")
        for move in cached_moves:
            pos = self._parse_position(move['position'])
            if pos:
                row, col = pos
                piece = self.PIECES[self.current_turn]
                self.board.place_piece(row, col, piece)
                self.move_count += 1
                self.moves.append({
                    'move_number': move['move_number'],
                    'player_id': move['player_id'],
                    'position': move['position'],
                    'timestamp': move['timestamp']
                })
                self.current_turn = 1 - self.current_turn
        self.board.display(self.config.get_board_style())
        print(f"Restored {self.move_count} moves. Continuing game...")
        # Continue the game loop
        while not self.game_over:
            current_player = self.players[self.current_turn]
            piece = self.PIECES[self.current_turn]
            color_name = "Black" if self.current_turn == 0 else "White"

            try:
                cmd = input(f"{color_name} ({current_player.name}) move: ").strip()
            except EOFError:
                self._save_and_exit()
                return

            if not cmd:
                print("Invalid input.")
                continue

            if cmd.lower() in ('resign', 'surrender'):
                winner = self.players[1 - self.current_turn]
                print(f"\n{current_player.name} surrendered! Winner: {winner.name}!")
                self.db.finish_game(
                    self.game_id, winner.player_id, time.time(),
                    self.move_count, [m['position'] for m in self.moves[:5]]
                )
                self.game_over = True
                return

            if cmd.lower() == 'undo':
                if self.can_undo and self.last_move:
                    lr, lc = self.last_move
                    self.board.remove_piece(lr, lc)
                    self.moves.pop()
                    self.move_count -= 1
                    self.current_turn = 1 - self.current_turn
                    self.can_undo = False
                    self.last_move = None
                    print("Undo successful!")
                    self.board.display(self.config.get_board_style())
                else:
                    print("Cannot undo: no move to undo or already undone once.")
                continue

            pos = self._parse_position(cmd)
            if pos is None:
                print("Invalid coordinate format.")
                continue

            row, col = pos
            if not self._is_valid_move(row, col):
                print("Invalid move: position is already occupied or out of bounds.")
                continue

            self.board.place_piece(row, col, piece)
            self.move_count += 1
            self.moves.append({
                'move_number': self.move_count,
                'player_id': current_player.player_id,
                'position': cmd.upper(),
                'timestamp': time.time()
            })
            self.last_move = (row, col)
            self.can_undo = True
            self._cache_moves_if_needed()
            self.board.display(self.config.get_board_style())

            if self._check_win(row, col):
                print(f"\nCongratulations! {current_player.name} ({color_name}) wins!")
                self.db.finish_game(
                    self.game_id, current_player.player_id, time.time(),
                    self.move_count, [m['position'] for m in self.moves[:5]]
                )
                self.game_over = True
                return

            self.current_turn = 1 - self.current_turn
