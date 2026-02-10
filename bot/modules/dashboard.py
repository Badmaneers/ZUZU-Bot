from flask import Blueprint, render_template, jsonify, request, send_file
import os
import json
import logging
from config import DATA_DIR, STATE_DIR, ROOT_DIR, LOG_FILE

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates', static_folder='../static')

# Paths
GROUPS_FILE = os.path.join(STATE_DIR, "groups.txt")
PROMPT_FILE = os.path.join(DATA_DIR, "prompt.txt")
BADWORDS_FILE = os.path.join(DATA_DIR, "badwords.txt")
FUN_FILE = os.path.join(DATA_DIR, "fun.json")
LOG_PATH = os.path.join(ROOT_DIR, "bot.log")

def get_stats():
    try:
        with open(GROUPS_FILE, 'r') as f:
            group_count = len(f.readlines())
    except FileNotFoundError:
        group_count = 0
    return {"groups": group_count}

@dashboard_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@dashboard_bp.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@dashboard_bp.route('/api/logs')
def api_logs():
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                lines = f.readlines()
                return jsonify({"logs": lines[-100:]}) # Last 100 lines
        return jsonify({"logs": []})
    except Exception as e:
        return jsonify({"error": str(e)})

@dashboard_bp.route('/api/data/<type>', methods=['GET', 'POST'])
def api_data(type):
    if type == 'prompt':
        file_path = PROMPT_FILE
    elif type == 'badwords':
        file_path = BADWORDS_FILE
    elif type == 'fun':
        file_path = FUN_FILE
    else:
        return jsonify({"error": "Invalid type"}), 400

    if request.method == 'GET':
        try:
            if type == 'fun':
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        return jsonify(json.load(f))
                return jsonify({"roasts": [], "motivations": []})
            else:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        return jsonify({"content": f.read()})
                return jsonify({"content": ""})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if request.method == 'POST':
        try:
            data = request.json
            if type == 'fun':
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4)
            else:
                content = data.get('content', '')
                with open(file_path, 'w') as f:
                    f.write(content)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
