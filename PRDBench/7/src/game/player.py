"""Player management module."""

MAX_PLAYERS = 10


class Player:
    def __init__(self, player_id, name):
        self.player_id = player_id
        self.name = name

    def __repr__(self):
        return f"Player({self.player_id}, {self.name})"


class PlayerManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_player(self, name):
        players = self.db.get_all_players()
        if len(players) >= MAX_PLAYERS:
            return None
        # Check duplicate name
        for p in players:
            if p['name'] == name:
                return None
        player_id = self.db.add_player(name)
        if player_id is not None:
            return Player(player_id, name)
        return None

    def delete_player(self, name):
        return self.db.delete_player(name)

    def get_all_players(self):
        rows = self.db.get_all_players()
        return [Player(r['player_id'], r['name']) for r in rows]

    def get_player_by_index(self, index):
        players = self.get_all_players()
        if 0 <= index < len(players):
            return players[index]
        return None

    def get_player_by_name(self, name):
        for p in self.get_all_players():
            if p.name == name:
                return p
        return None
