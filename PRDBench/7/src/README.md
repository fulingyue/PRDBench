# Command Line Board Game Battle and Data Statistics System

A multifunctional board game application supporting Gomoku and Chinese Chess with battle data recording and analysis.

## Features

- **Game Lobby**: Main menu with Start New Match, Continue Match, View Historical Data, Data Analysis Center, System Configuration, and Exit
- **Gomoku**: 15x15 board, coordinate input (e.g., H8), win detection, undo, and surrender
- **Chinese Chess**: 9x10 board with full piece movement rules including horse leg blocking, elephant eye blocking, cannon platform jumping
- **Data Recording**: SQLite-based storage with auto-save every 5 moves and crash recovery
- **Data Analysis**: 7-day frequency ranking, win rate statistics, opening heatmap, CSV export
- **System Configuration**: Player management (max 10), board display styles (compact/standard/expanded), data clearing

## Usage

```bash
python main.py
```

## Project Structure

```
src/
├── main.py              # Main entry point
├── data/
│   ├── database.py      # SQLite database manager
│   └── analytics.py     # Data analysis center
├── game/
│   ├── player.py        # Player management
│   ├── gomoku.py        # Gomoku game logic
│   └── xiangqi.py       # Chinese Chess game logic
└── utils/
    └── config.py        # Configuration manager
```
