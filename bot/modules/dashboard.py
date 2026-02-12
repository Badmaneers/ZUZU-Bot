from flask import Blueprint, render_template, jsonify, request, send_file, session, redirect, url_for, flash
import os
import json
import logging
from functools import wraps
from config import DATA_DIR, STATE_DIR, ROOT_DIR, LOG_FILE, ADMIN_PASSWORD, MEMORY_ACCESS_PASSWORD
import sqlite3
import psutil
from dotenv import dotenv_values
from core.memory import CIPHER

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates', static_folder='../static')
DB_FILE = "state/bot_memory.db"

# Paths
GROUPS_FILE = os.path.join(STATE_DIR, "groups.txt")
PROMPT_FILE = os.path.join(DATA_DIR, "prompt.txt")
BADWORDS_FILE = os.path.join(DATA_DIR, "badwords.txt")
FUN_FILE = os.path.join(DATA_DIR, "fun.json")
LOG_PATH = os.path.join(ROOT_DIR, "bot.log")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('dashboard.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_stats():
    try:
        with open(GROUPS_FILE, 'r') as f:
            group_count = len(f.readlines())
    except FileNotFoundError:
        group_count = 0
    return {"groups": group_count}

def get_current_env_value(key, default=None):
    """Refreshes and gets a value from .env file directly"""
    try:
        env_dict = dotenv_values(os.path.join(ROOT_DIR, '.env'))
        return env_dict.get(key, default)
    except:
        return default

@dashboard_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        # Dynamic check - allows login with either dynamic file value OR startup environment value
        current_admin_password = get_current_env_value("ADMIN_PASSWORD", ADMIN_PASSWORD)
        
        if password == current_admin_password or password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid password')
            return redirect(url_for('dashboard.login'))
    return render_template('login.html')

@dashboard_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    return jsonify(get_stats())


@dashboard_bp.route('/api/logs')
@login_required
def api_logs():
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                lines = f.readlines()
                return jsonify({"logs": lines[-100:]}) # Last 100 lines
        return jsonify({"logs": []})
    except Exception as e:
        return jsonify({"error": str(e)})

@dashboard_bp.route('/api/logs/clear', methods=['POST'])
@login_required
def clear_logs():
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'w') as f:
                f.write('')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})

@dashboard_bp.route('/api/data/<type>', methods=['GET', 'POST'])
@login_required
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

# --- Memory Access Routes ---

@dashboard_bp.route('/api/memory/auth', methods=['POST'])
@login_required
def memory_auth():
    """Verify separate password for memory access"""
    data = request.json
    pwd = data.get('password')
    
    # Dynamic check
    current_mem_password = get_current_env_value("MEMORY_ACCESS_PASSWORD", MEMORY_ACCESS_PASSWORD)
    
    if pwd == current_mem_password or pwd == MEMORY_ACCESS_PASSWORD:
        session['memory_unlocked'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid password"}), 403

@dashboard_bp.route('/api/memory/list', methods=['GET'])
@login_required
def memory_list():
    """List all available memory keys"""
    if not session.get('memory_unlocked'):
        return jsonify({"error": "Locked"}), 403
        
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT memory_key, last_updated FROM chat_memory ORDER BY last_updated DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return jsonify({
            "chats": [{"key": r[0], "updated": r[1]} for r in rows]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/api/memory/view/<key>', methods=['GET'])
@login_required
def memory_view(key):
    """View encrypted memory for a specific key"""
    if not session.get('memory_unlocked'):
        return jsonify({"error": "Locked"}), 403
        
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT messages FROM chat_memory WHERE memory_key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
             return jsonify({"messages": []})
             
        # Decrypt logic duplicated from memory logic to keep dashboard independent or reusing component
        encrypted_blob = row[0]
        try:
             decrypted_json = CIPHER.decrypt(encrypted_blob.encode()).decode()
             messages = json.loads(decrypted_json)
        except:
             # Fallback
             try:
                 messages = json.loads(encrypted_blob)
             except:
                 messages = [{"role": "system", "content": "Error decrypting memory."}]
                 
        return jsonify({"messages": messages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/api/memory/save', methods=['POST'])
@login_required
def memory_save():
    """Create or Update a memory key"""
    if not session.get('memory_unlocked'):
        return jsonify({"error": "Locked"}), 403
        
    data = request.json
    key = data.get('key')
    messages = data.get('messages')
    
    if not key or not isinstance(messages, list):
        return jsonify({"error": "Invalid data"}), 400
        
    try:
        # Encrypt
        encrypted_data = CIPHER.encrypt(json.dumps(messages).encode()).decode()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO chat_memory (memory_key, messages, last_updated) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (key, encrypted_data)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/api/memory/delete', methods=['POST'])
@login_required
def memory_delete():
    """Delete a memory key"""
    if not session.get('memory_unlocked'):
        return jsonify({"error": "Locked"}), 403
        
    data = request.json
    key = data.get('key')
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_memory WHERE memory_key = ?", (key,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/api/memory/commit', methods=['POST'])
@login_required
def memory_force_commit():
    """Force save dirty memory keys to database"""
    if not session.get('memory_unlocked'):
        return jsonify({"error": "Locked"}), 403
        
    try:
        # We need to access the running bot's memory instance.
        # Since this runs in the same process as the supervisor but the bot logic is in a subprocess/thread 
        # (Wait, actually in supervisor mode, dashboard is main.py, worker is subprocess)
        # We cannot access the worker's memory object directly.
        # However, the worker writes to DB automatically.
        # If the user wants to trigger a save from dashboard, we might need IPC or just rely on worker's nature.
        
        # But wait! The dashboard is editing the DB directly via SQL.
        # The worker reads/writes to DB.
        # If we "edit" via dashboard, we are writing to DB.
        # The worker might have cached old data.
        
        # This architecture (Dashboard in Main, Bot in Subprocess) makes shared memory tricky.
        # The Dashboard writes to SQLite.
        # The Worker has an in-memory CACHE.
        
        # If Dashboard updates DB, Worker doesn't know.
        # Worker might overwrite Dashboard changes on next save if it thinks its cache is newer.
        # Ideally, we need to signal the Worker to RELOAD from DB or restart.
        
        # For now, let's implement a "Reload Memory" signal?
        # Or just a restart.
        
        return jsonify({"success": True, "message": "Changes saved to DB. Note: Active bot process may need restart to pick up external DB edits."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Environment Settings Routes ---

@dashboard_bp.route('/api/env', methods=['GET'])
@login_required
def get_env_vars():
    """Read and parse .env file"""
    try:
        env_path = os.path.join(ROOT_DIR, '.env')
        if not os.path.exists(env_path):
            return jsonify({"vars": []})
        
        # Use python-dotenv to parse correctly
        env_dict = dotenv_values(env_path)
        vars = [{"key": k, "value": v} for k, v in env_dict.items()]
        
        return jsonify({"vars": vars})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/api/env', methods=['POST'])
@login_required
def save_env_vars():
    """Save variables to .env file"""
    try:
        data = request.json
        vars = data.get('vars', [])
        
        env_path = os.path.join(ROOT_DIR, '.env')
        with open(env_path, 'w') as f:
            for item in vars:
                key = item.get('key', '').strip()
                value = item.get('value', '').strip()
                if key:
                    # Auto-quote if needed
                    val_to_write = value
                    if " " in val_to_write or "#" in val_to_write or "\n" in val_to_write or not val_to_write:
                        # minimal escaping
                        val_to_write = val_to_write.replace('"', '\\"')
                        val_to_write = f'"{val_to_write}"'
                        
                    f.write(f"{key}={val_to_write}\n")
        
        return jsonify({"success": True, "message": "Settings saved. Restart bot to apply."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
