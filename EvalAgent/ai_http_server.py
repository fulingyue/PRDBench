import random
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return 'Service is healthy', 200

@app.route('/info', methods=['GET'])
def info():
    return jsonify({
        'ai_name': 'Gemini AI',
        'ai_author': 'Google',
    })

@app.route('/start', methods=['POST'])
def start():
    data = request.get_json()
    board_size = data['board_size']
    return jsonify({'message': 'Game started'})

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    board = data['board']
    moves = data['moves']
    
    # Find all empty cells
    empty_cells = []
    for r in range(len(board)):
        for c in range(len(board[r])):
            if board[r][c] == 0:
                empty_cells.append([r, c])
    
    # Choose a random empty cell
    move = random.choice(empty_cells)
    
    return jsonify({'move': move})

@app.route('/end', methods=['POST'])
def end():
    data = request.get_json()
    return jsonify({'message': 'Game ended'})

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=45006)
    parser.add_argument('--ai_id', type=str, default='ADK_gemini')
    parser.add_argument('--ai_name', type=str, default='Gemini AI')
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port)
