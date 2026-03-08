#!/usr/bin/env python3
"""
NVIDIA Gravity Engine - Telegram Remote Controller
Uses raw requests API to avoid Python 3.8 SSL issues with telegram library
"""
import logging
import os
import subprocess
import sys
import time
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load settings
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
try:
    AUTHORIZED_USER_ID = int(os.getenv('AUTHORIZED_USER_ID', '0'))
except (ValueError, TypeError):
    AUTHORIZED_USER_ID = 0

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

is_running = False


def send_message(chat_id, text):
    """Send a message via Telegram API using requests with retry"""
    # Try with Markdown first, fall back to plain text if parsing fails
    for parse_mode in ["Markdown", None]:
        for attempt in range(3):
            try:
                payload = {"chat_id": chat_id, "text": text}
                if parse_mode:
                    payload["parse_mode"] = parse_mode
                resp = requests.post(
                    f"{API_URL}/sendMessage",
                    json=payload,
                    timeout=30
                )
                if resp.status_code == 200:
                    logger.info(f"📤 Message sent to {chat_id}")
                    return True
                elif resp.status_code == 400 and "parse entities" in resp.text:
                    logger.warning(f"⚠️ Markdown failed, retrying as plain text")
                    break  # Break retry loop, try without Markdown
                else:
                    logger.error(f"❌ Send failed: {resp.status_code} {resp.text}")
            except Exception as e:
                logger.error(f"❌ Send error (attempt {attempt+1}/3): {e}")
                time.sleep(2)
        else:
            continue  # Only if retry loop wasn't broken
        continue  # Move to next parse_mode (None)
    return False


def get_updates(offset=None):
    """Get updates from Telegram using long polling"""
    try:
        params = {"timeout": 30, "allowed_updates": ["message"]}
        if offset:
            params["offset"] = offset
        resp = requests.get(f"{API_URL}/getUpdates", params=params, timeout=60)
        if resp.status_code == 200:
            return resp.json().get("result", [])
    except requests.exceptions.Timeout:
        pass  # Normal for long polling
    except Exception as e:
        logger.error(f"❌ Poll error: {e}")
        time.sleep(5)
    return []


def handle_command(chat_id, user_id, command):
    """Handle incoming commands"""
    if user_id != AUTHORIZED_USER_ID:
        logger.warning(f"❌ Unauthorized: {user_id}")
        return

    if command == "/start":
        send_message(chat_id,
            "🌊 *NVIDIA Gravity Controller Ready*\n\n"
            "📋 Commands:\n"
            "/run - Run prediction engine\n"
            "/status - Check system status"
        )

    elif command == "/run":
        global is_running
        if is_running:
            send_message(chat_id, "⚠️ Engine already running, please wait...")
            return

        # Use fake_main.py for testing, main.py for production
        test_mode = os.path.exists(os.path.join(PROJECT_DIR, 'fake_main.py'))
        script_name = 'fake_main.py' if test_mode else 'main.py'
        script_path = os.path.join(PROJECT_DIR, script_name)
        if not os.path.exists(script_path):
            send_message(chat_id, "❌ Script not found!")
            return

        venv_python = os.path.join(PROJECT_DIR, '.venv', 'Scripts', 'python.exe')
        python_exe = venv_python if os.path.exists(venv_python) and not test_mode else sys.executable

        # Run in a thread so polling continues
        def run_engine():
            global is_running
            log_file = os.path.join(PROJECT_DIR, 'logs', 'main_output.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            try:
                is_running = True
                start_time = datetime.now().strftime('%H:%M:%S')
                mode = "🧪 TEST MODE" if test_mode else "🔴 LIVE"
                send_message(chat_id, f"Starting Analysis...\n{start_time}\n{mode}")
                logger.info(f"🚀 Running: {python_exe} {script_name}")

                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'

                # Stream output to log file in real-time
                with open(log_file, 'w', encoding='utf-8') as f:
                    header = f"\n{'='*60}\nRUN STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}\n"
                    f.write(header)
                    f.flush()

                    proc = subprocess.Popen(
                        [python_exe, script_path],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding='utf-8', errors='replace',
                        cwd=PROJECT_DIR, env=env
                    )

                    full_output = []
                    for line in proc.stdout:
                        f.write(line)
                        f.flush()
                        full_output.append(line)

                    proc.wait(timeout=600)
                    
                    footer = f"\n{'='*60}\nRUN FINISHED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Exit: {proc.returncode}\n{'='*60}\n"
                    f.write(footer)
                    f.flush()

                output_text = ''.join(full_output)
                logger.info(f"✅ Done. Exit: {proc.returncode}")

                if proc.returncode == 0:
                    results = parse_results(output_text)
                    send_message(chat_id, f"Success!\n\n{results}")
                else:
                    err = output_text[-400:] if output_text else "No error"
                    send_message(chat_id, f"Failed (code {proc.returncode})\n\n{err}")

            except subprocess.TimeoutExpired:
                proc.kill()
                send_message(chat_id, "Timeout! Over 10 minutes")
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                send_message(chat_id, f"Error: {str(e)}")
            finally:
                is_running = False

        threading.Thread(target=run_engine, daemon=True).start()

    elif command == "/status":
        status = "⚡ Running..." if is_running else "💤 Idle"
        send_message(chat_id, f"📊 *Status:* {status}")


def parse_results(output):
    """Parse main.py output into a clean Telegram summary"""
    try:
        lines = output.split('\n')
        data = {}
        last_section = None
        for line in lines:
            l = line.strip()
            if "HYBRID PREDICTION" in l:
                last_section = 'hybrid'
            elif "ML OPENING PREDICTION" in l:
                last_section = 'opening'
            elif "ML PREDICTION" in l and "VALIDATION" in l:
                last_section = 'ml'
            elif l.startswith("Articles:"):
                data['articles'] = l.split(":", 1)[1].strip()
            elif "ARTICLE CLASSIFICATION:" in l:
                # "ARTICLE CLASSIFICATION: 3 Company, 2 Macro"
                part = l.split(":", 1)[1].strip()
                data['classification'] = part
            elif l.startswith("Company:") and 'company_sent' not in data:
                data['company_sent'] = l.split(":", 1)[1].strip()
            elif l.startswith("Macro:") and 'macro_sent' not in data:
                data['macro_sent'] = l.split(":", 1)[1].strip()
            elif l.startswith("Trading Day:"):
                data['date'] = l.split(":", 1)[1].strip()
            elif "OPENING PREDICTION:" in l and "ML PREDICTION:" not in l:
                data['opening_pred'] = l.split("OPENING PREDICTION:", 1)[1].strip()
            elif "ML PREDICTION:" in l and "VALIDATION" not in l:
                data['ml_pred'] = l.split("ML PREDICTION:", 1)[1].strip()
            elif "HYBRID SIGNAL:" in l:
                data['hybrid_pred'] = l.split("HYBRID SIGNAL:", 1)[1].strip()
            elif l.startswith("Technical Score:") and last_section == 'hybrid':
                data['tech_score'] = l.split(":", 1)[1].strip()
            elif l.startswith("Sentiment Score:") and last_section == 'hybrid':
                data['sent_score'] = l.split(":", 1)[1].strip()
            elif l.startswith("Strategy:") and last_section == 'hybrid':
                data['strategy'] = l.split(":", 1)[1].strip()
            elif l.startswith("Confidence:"):
                conf = l.split(":", 1)[1].strip()
                if last_section == 'hybrid' and 'hybrid_conf' not in data:
                    data['hybrid_conf'] = conf
                elif last_section == 'ml' and 'ml_conf' not in data:
                    data['ml_conf'] = conf
                elif last_section == 'opening' and 'opening_conf' not in data:
                    data['opening_conf'] = conf

        articles = data.get('articles', '?')
        cls = data.get('classification', '')
        date = data.get('date', '?')
        ml = data.get('ml_pred', 'N/A')
        ml_conf = data.get('ml_conf', 'N/A')
        hybrid = data.get('hybrid_pred', 'N/A')
        hybrid_conf = data.get('hybrid_conf', 'N/A')
        opening = data.get('opening_pred', 'N/A')
        opening_conf = data.get('opening_conf', 'N/A')
        tech_score = data.get('tech_score', 'N/A')
        sent_score = data.get('sent_score', 'N/A')
        strategy = data.get('strategy', 'N/A')

        msg = (
            f"📅 Date: {date}\n"
            f"📰 Articles: {articles} ({cls})\n"
            f"\n"
            f"🔬 Hybrid: {hybrid}\n"
            f"   Confidence: {hybrid_conf}\n"
            f"\n"
            f"📊 Technical Score: {tech_score}\n"
            f"📰 Sentiment Score: {sent_score}\n"
            f"⚖️ Weights: {strategy}\n"
            f"\n"
            f"🎯 ML Close: {ml}\n"
            f"   Confidence: {ml_conf}\n"
            f"\n"
            f"🌅 ML Opening: {opening}\n"
            f"   Confidence: {opening_conf}"
        )
        return msg
    except Exception as e:
        return f"Completed (parse error: {e})"


def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env"); sys.exit(1)
    if not AUTHORIZED_USER_ID:
        print("❌ AUTHORIZED_USER_ID not set in .env"); sys.exit(1)

    print("🤖 NVIDIA Gravity Bot")
    print(f"🔑 Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"👤 User ID: {AUTHORIZED_USER_ID}")
    print(f"📁 Dir: {PROJECT_DIR}")
    print()

    # Quick test with retries (Python 3.8 SSL drops connections randomly)
    bot_info = None
    for attempt in range(5):
        try:
            resp = requests.get(f"{API_URL}/getMe", timeout=15)
            bot_info = resp.json()["result"]
            print(f"✅ Bot: {bot_info['first_name']} (@{bot_info['username']})")
            break
        except Exception as e:
            print(f"⚠️ Connection attempt {attempt+1}/5: {e}")
            time.sleep(3)
    if not bot_info:
        print("❌ Cannot reach Telegram after 5 attempts")
        sys.exit(1)

    # Clear pending updates (with retry)
    for attempt in range(3):
        try:
            requests.get(f"{API_URL}/getUpdates", params={"offset": -1, "timeout": 0}, timeout=15)
            break
        except Exception:
            time.sleep(2)

    print("\n🚀 Bot is running! Waiting for commands...")
    print("💬 Send /start to @AliNvidia_bot")
    print("🛑 Press Ctrl+C to stop\n")

    offset = None
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                user_id = msg.get("from", {}).get("id")

                if text and chat_id and user_id:
                    logger.info(f"📩 {text} from user {user_id}")
                    handle_command(chat_id, user_id, text.split()[0])

        except KeyboardInterrupt:
            print("\n👋 Bot stopped")
            break
        except Exception as e:
            logger.error(f"❌ Loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()