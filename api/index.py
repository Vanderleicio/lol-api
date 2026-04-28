from flask import Flask, jsonify, request
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'data', '2026-league-data.db')

def get_db_connection():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)

    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/matches', methods=['GET'])
def get_matches():
    """
    /api/matches
    /api/matches?league=LCK
    /api/matches?player=Chovy
    /api/matches?league=LCK&player=Chovy&patch=14.1
    """
    try:
        conn = get_db_connection()
        
        league_filter = request.args.get('league')
        player_filter = request.args.get('player')
        patch_filter = request.args.get('patch')

        base_query = '''
            SELECT DISTINCT m.id, l.league_name, m.team_1, m.team_2, m.score_1, m.score_2, m.patch, m.date 
            FROM matches m
            JOIN leagues l ON m.league_id = l.id
            LEFT JOIN games g ON m.id = g.match_id
            WHERE 1=1
        '''

        query_params = []
 
        if league_filter:
            base_query += " AND l.league_name = ? COLLATE NOCASE"
            query_params.append(league_filter)

        if patch_filter:
            base_query += " AND m.patch = ?"
            query_params.append(patch_filter)

        if player_filter:
            search_string = f'%"{player_filter}"%'
            base_query += " AND (g.blue_players LIKE ? OR g.red_players LIKE ?)"
            query_params.extend([search_string, search_string])

        base_query += " ORDER BY m.date DESC LIMIT 100"

        matches = conn.execute(base_query, query_params).fetchall()
        conn.close()

        if not matches:
            return jsonify({"mensagem": "Nenhuma partida encontrada com esses filtros."}), 404

        return jsonify([dict(match) for match in matches]), 200

    except sqlite3.Error as e:
        return jsonify({"erro": "Erro no banco de dados", "detalhes": str(e)}), 500
    

@app.route('/api/leagues', methods=['GET'])
def get_all_tournaments():
    try:
        conn = get_db_connection()
        
        query = 'SELECT id, league_name FROM leagues LIMIT 100'
        
        matches = conn.execute(query).fetchall()
        conn.close()

        return jsonify([dict(match) for match in matches]), 200

    except sqlite3.Error as e:
        return jsonify({"erro": "Falha ao acessar o banco de dados", "detalhes": str(e)}), 500

@app.route('/api/games/<id_match>', methods=['GET'])
def get_games_by_match(id_match):
    try:
        conn = get_db_connection()
        
        query = 'SELECT * FROM games WHERE match_id = ?'
        games = conn.execute(query, (id_match,)).fetchall()
        conn.close()

        if not games:
            return jsonify({"mensagem": "Nenhum dado encontrado para este parâmetro."}), 404

        return jsonify([dict(game) for game in games]), 200

    except sqlite3.Error as e:
        return jsonify({"erro": "Erro no banco de dados", "detalhes": str(e)}), 500

@app.route('/api/games/<player>', methods=['GET'])
def get_games_by_player(player):
    try:
        conn = get_db_connection()
        
        query = 'SELECT * FROM games WHERE ? in blue_players OR ? in red_players'
        games = conn.execute(query, (player,)).fetchall()
        conn.close()

        if not games:
            return jsonify({"mensagem": "Nenhum dado encontrado para este parâmetro."}), 404

        return jsonify([dict(game) for game in games]), 200

    except sqlite3.Error as e:
        return jsonify({"erro": "Erro no banco de dados", "detalhes": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=8080)