from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = {
        "wins": 150,
        "kd": 2.5,
        "matches": 300
    }
    return jsonify([stats['wins'], stats['kd'], stats['matches']])

if __name__ == '__main__':
    app.run(debug=True)
