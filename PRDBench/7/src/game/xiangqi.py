"""Chinese Chess (Xiangqi) game module."""

import time
import json

# Piece definitions
RED_PIECES = {
    'r_chariot': '车', 'r_horse': '马', 'r_elephant': '相',
    'r_advisor': '仕', 'r_commander': '帅', 'r_cannon': '炮', 'r_soldier': '兵'
}
BLACK_PIECES = {
    'b_chariot': '車', 'b_horse': '馬', 'b_elephant': '象',
    'b_advisor': '士', 'b_general': '将', 'b_cannon': '砲', 'b_soldier': '卒'
}

INITIAL_LAYOUT = {
    (0, 0): 'b_chariot', (0, 1): 'b_horse', (0, 2): 'b_elephant',
    (0, 3): 'b_advisor', (0, 4): 'b_general', (0, 5): 'b_advisor',
    (0, 6): 'b_elephant', (0, 7): 'b_horse', (0, 8): 'b_chariot',
    (2, 1): 'b_cannon', (2, 7): 'b_cannon',
    (3, 0): 'b_soldier', (3, 2): 'b_soldier', (3, 4): 'b_soldier',
    (3, 6): 'b_soldier', (3, 8): 'b_soldier',
    (6, 0): 'r_soldier', (6, 2): 'r_soldier', (6, 4): 'r_soldier',
    (6, 6): 'r_soldier', (6, 8): 'r_soldier',
    (7, 1): 'r_cannon', (7, 7): 'r_cannon',
    (9, 0): 'r_chariot', (9, 1): 'r_horse', (9, 2): 'r_elephant',
    (9, 3): 'r_advisor', (9, 4): 'r_commander', (9, 5): 'r_advisor',
    (9, 6): 'r_elephant', (9, 7): 'r_horse', (9, 8): 'r_chariot',
}


def get_piece_color(piece):
    if piece is None:
        return None
    if isinstance(piece, str):
        if piece.startswith('r_') or piece == 'Commander':
            return 'red'
        if piece.startswith('b_') or piece == 'General':
            return 'black'
        if piece[0].islower():
            return 'red'
        return 'black'
    return None


def get_piece_type(piece):
    if piece is None:
        return None
    if isinstance(piece, str):
        if '_' in piece:
            return piece.split('_', 1)[1]
        mapping = {
            'Commander': 'commander', 'General': 'general',
        }
        return mapping.get(piece, 'unknown')
    return None


class XiangqiBoard:
    ROWS, COLS = 10, 9

    def __init__(self):
        self.grid = [[None for _ in range(self.COLS)] for _ in range(self.ROWS)]
        for (r, c), piece in INITIAL_LAYOUT.items():
            self.grid[r][c] = piece

    def place_piece(self, row, col, piece):
        self.grid[row][col] = piece

    def get_piece(self, row, col):
        if 0 <= row < self.ROWS and 0 <= col < self.COLS:
            return self.grid[row][col]
        return None

    def display(self, style='standard'):
        spacing = {'compact': '', 'standard': ' ', 'expanded': '  '}
        sep = spacing.get(style, ' ')
        col_labels = "  " + sep.join(str(i) for i in range(self.COLS))
        print(col_labels)
        for row in range(self.ROWS):
            if row == 5:
                print("  " + "=" * (len(sep) * (self.COLS - 1) + self.COLS) + "  Chu River Han Border")
            line = f"{row} "
            cells = []
            for col in range(self.COLS):
                piece = self.grid[row][col]
                if piece is None:
                    cells.append('+')
                elif piece in RED_PIECES:
                    cells.append(RED_PIECES[piece])
                elif piece in BLACK_PIECES:
                    cells.append(BLACK_PIECES[piece])
                else:
                    cells.append('*')
            line += sep.join(cells)
            print(line)


class XiangqiGame:
    def __init__(self, player1, player2, db_manager, config_manager):
        self.players = [player1, player2]  # player1=red, player2=black
        self.board = XiangqiBoard()
        self.db = db_manager
        self.config = config_manager
        self.current_turn = 0  # 0=red, 1=black
        self.moves = []
        self.game_id = None
        self.move_count = 0
        self.game_over = False

    def _is_valid_move(self, fr, fc, tr, tc):
        if not (0 <= tr < 10 and 0 <= tc < 9):
            return False
        piece = self.board.get_piece(fr, fc)
        if piece is None:
            return False
        color = get_piece_color(piece)
        ptype = get_piece_type(piece)
        target = self.board.get_piece(tr, tc)
        target_color = get_piece_color(target)

        if target_color == color:
            return False

        dr, dc = tr - fr, tc - fc

        if ptype == 'chariot':
            if not self._is_straight_clear(fr, fc, tr, tc):
                return False
        elif ptype == 'horse':
            if not self._is_valid_horse(fr, fc, tr, tc):
                return False
        elif ptype == 'elephant':
            if not self._is_valid_elephant(fr, fc, tr, tc, color):
                return False
        elif ptype == 'advisor':
            if not self._is_valid_advisor(fr, fc, tr, tc, color):
                return False
        elif ptype in ('commander', 'general'):
            if not self._is_valid_general(fr, fc, tr, tc, color):
                return False
        elif ptype == 'cannon':
            if not self._is_valid_cannon(fr, fc, tr, tc, target):
                return False
        elif ptype == 'soldier':
            if not self._is_valid_soldier(fr, fc, tr, tc, color):
                return False
        else:
            return False

        # Check generals facing after move
        if not self._check_generals_after_move(fr, fc, tr, tc):
            return False

        return True

    def _is_straight_clear(self, fr, fc, tr, tc):
        if fr != tr and fc != tc:
            return False
        if fr == tr:
            step = 1 if tc > fc else -1
            for c in range(fc + step, tc, step):
                if self.board.grid[fr][c] is not None:
                    return False
        else:
            step = 1 if tr > fr else -1
            for r in range(fr + step, tr, step):
                if self.board.grid[r][fc] is not None:
                    return False
        return True

    def _count_between(self, fr, fc, tr, tc):
        count = 0
        if fr == tr:
            step = 1 if tc > fc else -1
            for c in range(fc + step, tc, step):
                if self.board.grid[fr][c] is not None:
                    count += 1
        elif fc == tc:
            step = 1 if tr > fr else -1
            for r in range(fr + step, tr, step):
                if self.board.grid[r][fc] is not None:
                    count += 1
        return count

    def _is_valid_horse(self, fr, fc, tr, tc):
        dr, dc = tr - fr, tc - fc
        valid_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)]
        if (dr, dc) not in valid_moves:
            return False
        # Check blocking leg
        if abs(dr) == 2:
            block_r = fr + (1 if dr > 0 else -1)
            if self.board.grid[block_r][fc] is not None:
                return False
        else:
            block_c = fc + (1 if dc > 0 else -1)
            if self.board.grid[fr][block_c] is not None:
                return False
        return True

    def _is_valid_elephant(self, fr, fc, tr, tc, color):
        dr, dc = tr - fr, tc - fc
        if abs(dr) != 2 or abs(dc) != 2:
            return False
        # Elephant cannot cross river
        if color == 'red' and tr < 5:
            return False
        if color == 'black' and tr > 4:
            return False
        # Check blocking eye
        mid_r = fr + dr // 2
        mid_c = fc + dc // 2
        if self.board.grid[mid_r][mid_c] is not None:
            return False
        return True

    def _is_valid_advisor(self, fr, fc, tr, tc, color):
        dr, dc = tr - fr, tc - fc
        if abs(dr) != 1 or abs(dc) != 1:
            return False
        # Must stay in palace
        if color == 'red':
            if not (7 <= tr <= 9 and 3 <= tc <= 5):
                return False
        else:
            if not (0 <= tr <= 2 and 3 <= tc <= 5):
                return False
        return True

    def _is_valid_general(self, fr, fc, tr, tc, color):
        dr, dc = tr - fr, tc - fc
        if abs(dr) + abs(dc) != 1:
            return False
        if color == 'red':
            if not (7 <= tr <= 9 and 3 <= tc <= 5):
                return False
        else:
            if not (0 <= tr <= 2 and 3 <= tc <= 5):
                return False
        return True

    def _is_valid_cannon(self, fr, fc, tr, tc, target):
        if fr != tr and fc != tc:
            return False
        between = self._count_between(fr, fc, tr, tc)
        if target is None:
            return between == 0
        else:
            return between == 1

    def _is_valid_soldier(self, fr, fc, tr, tc, color):
        dr, dc = tr - fr, tc - fc
        if abs(dr) + abs(dc) != 1:
            return False
        if color == 'red':
            if dr > 0:
                return False
            if fr > 4 and dc != 0:
                return False
        else:
            if dr < 0:
                return False
            if fr < 5 and dc != 0:
                return False
        return True

    def _check_generals_after_move(self, fr, fc, tr, tc):
        # Simulate move
        orig_src = self.board.grid[fr][fc]
        orig_dst = self.board.grid[tr][tc]
        self.board.grid[tr][tc] = orig_src
        self.board.grid[fr][fc] = None

        # Find generals
        red_gen = black_gen = None
        for r in range(10):
            for c in range(9):
                p = self.board.grid[r][c]
                if p is not None:
                    pt = get_piece_type(p)
                    pc = get_piece_color(p)
                    if pt == 'commander' or (pt == 'general' and pc == 'red'):
                        if pc == 'red':
                            red_gen = (r, c)
                    if pt == 'general' and pc == 'black':
                        black_gen = (r, c)
                    if p == 'Commander':
                        red_gen = (r, c)
                    if p == 'General':
                        black_gen = (r, c)

        # Undo
        self.board.grid[fr][fc] = orig_src
        self.board.grid[tr][tc] = orig_dst

        if red_gen and black_gen and red_gen[1] == black_gen[1]:
            col = red_gen[1]
            blocked = False
            min_r = min(red_gen[0], black_gen[0])
            max_r = max(red_gen[0], black_gen[0])
            # Use simulated state
            self.board.grid[tr][tc] = orig_src
            self.board.grid[fr][fc] = None
            for r in range(min_r + 1, max_r):
                if self.board.grid[r][col] is not None:
                    blocked = True
                    break
            self.board.grid[fr][fc] = orig_src
            self.board.grid[tr][tc] = orig_dst
            if not blocked:
                return False
        return True

    def _find_general(self, color):
        for r in range(10):
            for c in range(9):
                p = self.board.grid[r][c]
                if p:
                    pc = get_piece_color(p)
                    pt = get_piece_type(p)
                    if pc == color and pt in ('commander', 'general'):
                        return (r, c)
        return None

    def start(self):
        self.game_id = self.db.create_game_record(
            'xiangqi', self.players[0].player_id,
            self.players[1].player_id, time.time()
        )
        print("\n=== Chinese Chess Match Started ===")
        print(f"Red: {self.players[0].name}")
        print(f"Black: {self.players[1].name}")
        print("Enter moves like 'fr,fc,tr,tc' (e.g., '9,1,7,2') or 'resign'\n")
        self.board.display(self.config.get_board_style())

        while not self.game_over:
            current = self.players[self.current_turn]
            side = "Red" if self.current_turn == 0 else "Black"
            try:
                cmd = input(f"{side} ({current.name}) move: ").strip()
            except EOFError:
                return

            if not cmd:
                print("Invalid input.")
                continue

            if cmd.lower() in ('resign', 'surrender'):
                winner = self.players[1 - self.current_turn]
                print(f"{current.name} surrendered! Winner: {winner.name}!")
                self.db.finish_game(
                    self.game_id, winner.player_id, time.time(),
                    self.move_count, [])
                self.game_over = True
                return

            parts = cmd.replace(' ', ',').split(',')
            if len(parts) != 4:
                print("Invalid format. Use 'fr,fc,tr,tc' (e.g., '9,1,7,2').")
                continue
            try:
                fr, fc, tr, tc = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            except ValueError:
                print("Invalid coordinates.")
                continue

            piece = self.board.get_piece(fr, fc)
            if piece is None:
                print("No piece at that position.")
                continue
            piece_color = get_piece_color(piece)
            expected = 'red' if self.current_turn == 0 else 'black'
            if piece_color != expected:
                print(f"That's not your piece.")
                continue

            if not self._is_valid_move(fr, fc, tr, tc):
                print("Invalid move.")
                continue

            self.board.grid[tr][tc] = piece
            self.board.grid[fr][fc] = None
            self.move_count += 1
            self.moves.append(f"{fr},{fc}->{tr},{tc}")

            if self.move_count % 5 == 0:
                self.db.cache_moves(self.game_id, [{
                    'move_number': self.move_count,
                    'player_id': current.player_id,
                    'position': self.moves[-1],
                    'timestamp': time.time()
                }])

            self.board.display(self.config.get_board_style())

            # Check if opponent's general is captured
            opp_color = 'black' if self.current_turn == 0 else 'red'
            if self._find_general(opp_color) is None:
                print(f"{current.name} wins! Checkmate!")
                self.db.finish_game(
                    self.game_id, current.player_id, time.time(),
                    self.move_count, [])
                self.game_over = True
                return

            self.current_turn = 1 - self.current_turn
