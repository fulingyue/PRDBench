"""Configuration manager for board display and system settings."""


class ConfigManager:
    STYLES = {'compact': 0, 'standard': 1, 'expanded': 2}

    def __init__(self):
        self.board_style = 'standard'

    def set_board_style(self, style):
        if style in self.STYLES:
            self.board_style = style
            return True
        return False

    def get_board_style(self):
        return self.board_style
