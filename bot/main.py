import flask
import threading
import subprocess
import time
import sys
import logging
import psutil
from config import FLASK_SECRET_KEY, BASE_DIR
from dotenv import dotenv_values
import os
from modules.dashboard import dashboard_bp, login_required

# Configure basic logging for Main Process
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [SUPERVISOR] - %(message)s")

app = flask.Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.register_blueprint(dashboard_bp)

# Global variables for worker management
BOT_PROCESS = None
SHOULD_RESTART = True

def start_bot_worker():
    """Starts the bot worker process."""
    global BOT_PROCESS
    logging.info("Starting Bot Worker Process...")
    
    # Reload environment variables from .env file to ensure fresh config
    # We pass this modified environment to the subprocess
    env_updates = dotenv_values(os.path.join(BASE_DIR, '.env'))
    current_env = os.environ.copy()
    current_env.update(env_updates)
    
    # Run bot/worker.py using the same python executable
    BOT_PROCESS = subprocess.Popen([sys.executable, "bot/worker.py"], env=current_env)

def monitor_bot_worker():
    """Monitors the worker and restarts it if it crashes."""
    global BOT_PROCESS, SHOULD_RESTART
    while True:
        if SHOULD_RESTART:
            if BOT_PROCESS is None:
                start_bot_worker()
            elif BOT_PROCESS.poll() is not None:
                # Process exited
                exit_code = BOT_PROCESS.returncode
                logging.warning(f"Bot worker exited with code {exit_code}. Restarting in 3 seconds...")
                time.sleep(3)
                start_bot_worker()
        time.sleep(1)

def restart_bot_process():
    """Manually restarts the bot process"""
    global BOT_PROCESS
    if BOT_PROCESS:
        logging.info("Killing current bot process...")
        BOT_PROCESS.terminate()
        try:
            BOT_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            BOT_PROCESS.kill()
        BOT_PROCESS = None
    # monitor loop will pick it up

# --- Routes ---

@app.route('/')
def index():
    return flask.redirect('/dashboard')

@app.route('/api/control/restart', methods=['POST'])
@login_required
def api_restart():
    threading.Thread(target=restart_bot_process).start()
    return flask.jsonify({"success": True, "message": "Restart signal sent."})

@app.route('/api/control/status')
def api_status():
    status = "running" if BOT_PROCESS and BOT_PROCESS.poll() is None else "stopped"
    return flask.jsonify({"status": status})

@app.route('/api/control/stop', methods=['POST'])
@login_required
def api_stop():
    global BOT_PROCESS, SHOULD_RESTART
    SHOULD_RESTART = False
    if BOT_PROCESS:
        logging.info("Stopping bot process via dashboard...")
        BOT_PROCESS.terminate()
        try:
            BOT_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            BOT_PROCESS.kill()
        BOT_PROCESS = None
    return flask.jsonify({"success": True, "message": "Bot stopped."})

@app.route('/api/control/start', methods=['POST'])
@login_required
def api_start():
    global BOT_PROCESS, SHOULD_RESTART
    if BOT_PROCESS and BOT_PROCESS.poll() is None:
        return flask.jsonify({"success": False, "message": "Bot is already running."})
    SHOULD_RESTART = True
    threading.Thread(target=start_bot_worker).start()
    return flask.jsonify({"success": True, "message": "Bot start signal sent."})

@app.route('/api/stats/system')
@login_required
def api_stats_system():
    global BOT_PROCESS
    cpu_percent = 0.0
    memory_percent = 0.0
    
    if BOT_PROCESS and BOT_PROCESS.poll() is None:
        try:
            proc = psutil.Process(BOT_PROCESS.pid)
            # interval=None is non-blocking, but first call usually 0.0
            # Dividing by cpu_count to normalize 
            cpu_percent = proc.cpu_percent(interval=None) / psutil.cpu_count()
            
            # Memory percent
            memory_percent = proc.memory_percent()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    return flask.jsonify({
        "cpu": cpu_percent,
        "memory_percent": memory_percent
    })

def run_flask():
    # Use PORT from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start Monitor Thread
    threading.Thread(target=monitor_bot_worker, daemon=True).start()
    # Start Flask
    run_flask()
