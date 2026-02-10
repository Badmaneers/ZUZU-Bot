import flask
import threading
import subprocess
import time
import sys
import logging
from config import FLASK_SECRET_KEY, BASE_DIR
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
    # Run bot/worker.py using the same python executable
    BOT_PROCESS = subprocess.Popen([sys.executable, "bot/worker.py"])

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

def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    # Start Monitor Thread
    threading.Thread(target=monitor_bot_worker, daemon=True).start()
    # Start Flask
    run_flask()
