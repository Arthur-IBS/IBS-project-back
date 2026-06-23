import asyncio
import os
import time
import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
 
load_dotenv()
 
# Config from .env
LOG_FILE = os.getenv("AGENT_LOG_FILE", "logs/app.log")
POSITION_FILE = os.getenv("AGENT_POSITION_FILE", "agent_position.txt")
INTERVAL_SECONDS = int(os.getenv("AGENT_INTERVAL_SECONDS", "60"))
LOGSTASH_HOST = os.getenv("LOGSTASH_HOST", "localhost")
LOGSTASH_PORT = os.getenv("LOGSTASH_PORT", "5000")
LOGSTASH_URL = f"http://{LOGSTASH_HOST}:{LOGSTASH_PORT}"
MAX_RETRIES = int(os.getenv("AGENT_MAX_RETRIES", "3"))
RETRY_DELAY_SECONDS = int(os.getenv("AGENT_RETRY_DELAY", "5"))
APP_NAME = os.getenv("APP_NAME", "opsman")
 
IST = pytz.timezone('Asia/Kolkata')
 
 
def get_last_position():
    if os.path.exists(POSITION_FILE):
        with open(POSITION_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except:
                return 0
    return 0
 
 
def save_position(pos):
    with open(POSITION_FILE, "w") as f:
        f.write(str(pos))
 
 
def parse_line(line):
    try:
        line = line.strip()
        if not line.startswith('['):
            return None
        dt_str = line[1:20]
        timestamp = datetime.strptime(dt_str, "%d.%m.%Y %H:%M:%S")
        timestamp = IST.localize(timestamp)
 
        parts = line.split(', ', 2)
        if len(parts) < 3:
            return None
 
        thread = parts[1].strip()
        remainder = parts[2].strip()
        if not remainder:
            return None
 
        level = remainder[0]
        message = remainder[1:].strip()
 
        return {
            "log_timestamp": dt_str,
            "@timestamp": timestamp.isoformat(),
            "thread": thread,
            "level": level,
            "message": message,
            "application": APP_NAME
        }
    except:
        return None
 
 
def read_new_lines():
    if not os.path.exists(LOG_FILE):
        print(f"[WARN] Log file not found: {LOG_FILE}")
        return [], None
 
    last_pos = get_last_position()
    current_size = os.path.getsize(LOG_FILE)
 
    if current_size < last_pos:
        print("[INFO] Log file reset detected, reading from beginning")
        last_pos = 0
 
    if current_size == last_pos:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No new lines")
        return [], None
 
    docs = []
    current_line = ''
 
    with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(last_pos)
        for raw_line in f:
            line = raw_line.rstrip('\n')
            stripped = line.strip()
 
            if not stripped:
                continue
 
            if stripped.startswith('['):
                if current_line:
                    parsed = parse_line(current_line)
                    if parsed:
                        docs.append(parsed)
                current_line = stripped
            else:
                current_line += ' ' + stripped
 
        if current_line:
            parsed = parse_line(current_line)
            if parsed:
                docs.append(parsed)
 
        new_pos = f.tell()
 
    return docs, new_pos
 
 
def send_to_logstash(docs):
    if not docs:
        return True
 
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            for doc in docs:
                res = requests.post(
                    LOGSTASH_URL,
                    json=doc,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                if res.status_code not in (200, 201):
                    print(f"[WARN] Logstash returned {res.status_code}")
 
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent {len(docs)} lines to Logstash")
            return True
 
        except Exception as e:
            attempt += 1
            print(f"[ERROR] Logstash unreachable (attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                print(f"[INFO] Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"[FATAL] All retries failed. Will retry next cycle.")
                return False
 
    return False
 
 
async def run_agent():
    print("=" * 50)
    print("LogPro Agent Started")
    print(f"Log file: {LOG_FILE}")
    print(f"Logstash: {LOGSTASH_URL}")
    print(f"Application: {APP_NAME}")
    print(f"Interval: {INTERVAL_SECONDS} seconds")
    print(f"Max retries: {MAX_RETRIES}")
    print("=" * 50)
 
    while True:
        try:
            docs, new_pos = read_new_lines()
            if docs:
                success = send_to_logstash(docs)
                if success:
                    save_position(new_pos)
                else:
                    print(f"[INFO] Position not advanced — {len(docs)} lines will be retried next cycle")
        except Exception as e:
            print(f"[ERROR] Agent error: {e}")
 
        await asyncio.sleep(INTERVAL_SECONDS)
 
 
if __name__ == "__main__":
    asyncio.run(run_agent())
 